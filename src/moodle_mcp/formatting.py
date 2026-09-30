# shared helpers that turn raw Moodle data into Claude-friendly values
import html
import re
from datetime import datetime


def fmt_date(ts: int) -> str | None:
    """Moodle uses Unix timestamps; 0 means 'not set'."""
    if ts == 0:
        return None
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def html_to_text(raw: str) -> str:
    """Moodle HTML -> plain text (keeps line breaks)."""
    raw = re.sub(r"<br\s*/?>|</p>|</div>|</li>", "\n", raw or "", flags=re.I)
    raw = html.unescape(re.sub(r"<[^>]+>", "", raw))
    return re.sub(r"\n\s*\n+", "\n\n", raw).strip()


def browser_url(fileurl: str) -> str:
    """Web-service file links need the token; the plain pluginfile link works in a logged-in browser."""
    return fileurl.replace("/webservice/pluginfile.php", "/pluginfile.php")


def file_list(fileareas: list[dict]) -> list[dict]:
    return [
        {"filename": f["filename"], "url": browser_url(f["fileurl"])}
        for area in fileareas
        for f in area.get("files", [])
        # editpdf stores one preview image per page next to the annotated combined.pdf
        if not f["filename"].startswith("image_page")
    ]
