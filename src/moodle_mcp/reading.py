# the logic for reading the text of course files and Page activities
import io
import re
from urllib.parse import parse_qs, urlparse

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


def _file_text(url: str, year: int) -> tuple[str, str]:
    # browser links (pluginfile.php) need the web-service variant plus the token
    ws_url = re.sub(r"/(webservice/)?pluginfile\.php", "/webservice/pluginfile.php", url, count=1)
    response = _http.get(ws_url, params={"token": get_site(year).token}, follow_redirects=True)
    response.raise_for_status()
    kind = response.headers.get("content-type", "").split(";")[0]
    if kind == "application/json":  # Moodle reports missing files / no access this way
        raise MoodleError(response.json().get("error", "file could not be read"))
    if len(response.content) > MAX_BYTES:
        raise ValueError("File is larger than 25 MB; open it in the browser instead.")
    name = urlparse(url).path.rsplit("/", 1)[-1]
    if kind == "application/pdf":
        pages = PdfReader(io.BytesIO(response.content)).pages
        return name, "\n\n".join(f"--- page {i} ---\n{p.extract_text() or ''}" for i, p in enumerate(pages, 1))
    if kind.startswith("text/"):
        text = response.text
        return name, html_to_text(text) if kind == "text/html" else text
    raise ValueError(f"Can't read {kind or 'this'} files (e.g. slides as .pptx); only PDF, text and HTML. "
                     "Look for a PDF version, or open the url in the browser.")


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
