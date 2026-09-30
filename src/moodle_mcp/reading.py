# the logic for reading the text of course files and Page activities
import io
import re
from urllib.parse import parse_qs, unquote, urlparse

from docx import Document
from pptx import Presentation
from pypdf import PdfReader

from moodle_mcp.client import MoodleError, _http, call
from moodle_mcp.config import TOKENS, get_site
from moodle_mcp.formatting import html_to_text

MAX_CHARS = 30_000  # per call; longer texts are read in parts with `offset`
MAX_BYTES = 25 * 1024 * 1024


def _site_year(url: str) -> int:
    """Which configured year's site a URL belongs to. The token is only ever sent to that site."""
    for year in TOKENS:
        if url.startswith(get_site(year).url + "/"):
            return year
    raise ValueError("Only links to your Moodle site can be read (e.g. file urls from get_course_contents).")


def _page_text(cmid: int, year: int) -> tuple[str, str]:
    pages = call("mod_page_get_pages_by_courses", year=year)["pages"]
    page = next((p for p in pages if p["coursemodule"] == cmid), None)
    if page is None:
        raise ValueError(f"No Page activity with id {cmid}")
    return page["name"], html_to_text(page["intro"] + "\n\n" + page["content"])


PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _pdf(data: bytes) -> str:
    pages = PdfReader(io.BytesIO(data)).pages
    return "\n\n".join(f"--- page {i} ---\n{p.extract_text() or ''}" for i, p in enumerate(pages, 1))


def _pptx(data: bytes) -> str:
    slides = []
    for i, slide in enumerate(Presentation(io.BytesIO(data)).slides, 1):
        lines = [shape.text_frame.text for shape in slide.shapes if shape.has_text_frame and shape.text_frame.text.strip()]
        if slide.has_notes_slide and (notes := slide.notes_slide.notes_text_frame.text.strip()):
            lines.append(f"[notes] {notes}")
        slides.append(f"--- slide {i} ---\n" + "\n".join(lines))
    return "\n\n".join(slides)


def _docx(data: bytes) -> str:
    doc = Document(io.BytesIO(data))
    parts = [p.text for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        parts += [" | ".join(cell.text.strip() for cell in row.cells) for row in table.rows]
    return "\n".join(parts)


def _notebook(notebook: dict) -> str:
    cells = []
    for i, cell in enumerate(notebook.get("cells", []), 1):
        source = cell.get("source", "")
        text = "".join(source) if isinstance(source, list) else source
        cells.append(f"--- cell {i} ({cell.get('cell_type')}) ---\n{text}")
    return "\n\n".join(cells)


def _file_text(url: str, year: int) -> tuple[str, str]:
    # browser links (pluginfile.php) need the web-service variant plus the token
    ws_url = re.sub(r"/(webservice/)?pluginfile\.php", "/webservice/pluginfile.php", url, count=1)
    response = _http.get(ws_url, params={"token": get_site(year).token}, follow_redirects=True)
    response.raise_for_status()
    kind = response.headers.get("content-type", "").split(";")[0].strip()
    name = unquote(urlparse(url).path.rsplit("/", 1)[-1])
    if len(response.content) > MAX_BYTES:
        raise ValueError("File is larger than 25 MB; open it in the browser instead.")

    if kind == "application/json":
        data = response.json()
        if name.endswith(".ipynb") and isinstance(data, dict) and "cells" in data:
            return name, _notebook(data)
        if isinstance(data, dict) and "error" in data:  # Moodle reports missing files / no access this way
            raise MoodleError(data["error"])
        return name, response.text
    if kind == "application/pdf":
        return name, _pdf(response.content)
    if kind == PPTX:
        return name, _pptx(response.content)
    if kind == DOCX:
        return name, _docx(response.content)
    if kind.startswith("text/"):
        text = response.text.lstrip("﻿")  # some files start with a byte-order mark
        return name, html_to_text(text) if kind == "text/html" else text
    raise ValueError(f"Can't read {kind or 'this type of'} files; supported: PDF, PowerPoint (.pptx), "
                     "Word (.docx), notebooks (.ipynb), text, code and HTML. Open the url in the browser instead.")


def read_content(url: str, offset: int = 0) -> dict:
    year = _site_year(url)
    path = urlparse(url).path
    if "/mod/page/view.php" in path:
        cmid = int(parse_qs(urlparse(url).query)["id"][0])
        name, text = _page_text(cmid, year)
    elif "pluginfile.php" in path:
        name, text = _file_text(url, year)
    else:
        raise ValueError("Pass a file url (…/pluginfile.php/…) or a Page url (…/mod/page/view.php?id=…), "
                         "e.g. from get_course_contents or get_assignment.")
    part = text[offset:offset + MAX_CHARS]
    end = offset + len(part)
    return {
        "name": name,
        "text": part,
        "total_chars": len(text),
        **({"next_offset": end} if end < len(text) else {}),
    }
