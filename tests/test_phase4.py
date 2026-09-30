import io
import time

import httpx
import pytest
from pypdf import PdfWriter

from moodle_mcp.client import MoodleError
from moodle_mcp.deadlines import upcoming_deadlines
from moodle_mcp.reading import read_content
from moodle_mcp.search import search

NOW = int(time.time())
SITE = "https://moodle.test/2026"


def test_upcoming_deadlines(moodle):
    moodle.on("core_calendar_get_action_events_by_timesort", {"events": [{
        "name": "HW 1 is due", "activityname": "HW 1", "modulename": "assign", "course": {"fullname": "Networks"},
        "timesort": NOW + 3600, "overdue": False, "action": {"name": "Add submission"},
        "url": f"{SITE}/mod/assign/view.php?id=5",
    }]})
    [item] = upcoming_deadlines(days=7)
    assert item["name"] == "HW 1" and item["type"] == "assign" and item["course"] == "Networks"
    assert item["action"] == "Add submission" and item["overdue"] is False
    sent = moodle.calls[-1]
    assert int(sent["timesortfrom"]) >= NOW  # overdue items not requested by default
    assert int(sent["timesortto"]) - int(sent["timesortfrom"]) == 7 * 86400


def test_upcoming_deadlines_include_overdue_looks_back(moodle):
    moodle.on("core_calendar_get_action_events_by_timesort", {"events": []})
    upcoming_deadlines(include_overdue=True)
    assert int(moodle.calls[-1]["timesortfrom"]) < NOW - 29 * 86400  # ~30 days back


def test_search_shapes_results(moodle):
    moodle.on("core_search_get_results", {"totalcount": 1, "results": [{
        "title": "prep4exam &amp; more", "componentname": "mod_forum", "areaname": "post",
        "coursefullname": "Architectures", "content": "<p>" + "x" * 500 + "</p>", "timemodified": NOW,
        "docurl": f"{SITE}/mod/forum/discuss.php?d=1",
    }]})
    result = search("exam", page=2)
    r = result["results"][0]
    assert (result["total"], result["page"]) == (1, 2)
    assert r["title"] == "prep4exam & more" and r["kind"] == "mod_forum/post"
    assert len(r["snippet"]) == 300
    assert moodle.calls[-1]["query"] == "exam" and moodle.calls[-1]["page"] == "2"


def file_route(moodle, response):
    return moodle.router.get(url__regex=r"^https://moodle\.test/2026/webservice/pluginfile\.php/.*").mock(
        return_value=response)


def test_read_text_file_uses_token_and_webservice_url(moodle):
    route = file_route(moodle, httpx.Response(200, text="line 1\nline 2", headers={"content-type": "text/plain"}))
    result = read_content(f"{SITE}/pluginfile.php/1/mod_resource/content/1/notes.txt?forcedownload=1")
    assert result == {"name": "notes.txt", "text": "line 1\nline 2", "total_chars": 13}
    assert route.calls[0].request.url.params["token"] == "token-2026"


def test_read_pdf(moodle):
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    buffer = io.BytesIO()
    writer.write(buffer)
    file_route(moodle, httpx.Response(200, content=buffer.getvalue(), headers={"content-type": "application/pdf"}))
    result = read_content(f"{SITE}/pluginfile.php/1/mod_resource/content/1/slides.pdf")
    assert result["name"] == "slides.pdf"
    assert result["text"].startswith("--- page 1 ---")


def test_read_long_text_in_parts(moodle):
    file_route(moodle, httpx.Response(200, text="a" * 30_000 + "b" * 10, headers={"content-type": "text/plain"}))
    url = f"{SITE}/pluginfile.php/1/x.txt"
    first = read_content(url)
    assert first["next_offset"] == 30_000 and first["total_chars"] == 30_010
    second = read_content(url, offset=first["next_offset"])
    assert second["text"] == "b" * 10 and "next_offset" not in second


def test_read_unsupported_type(moodle):
    file_route(moodle, httpx.Response(200, content=b"PK", headers={"content-type": "application/vnd.ms-powerpoint"}))
    with pytest.raises(ValueError, match="only PDF, text and HTML"):
        read_content(f"{SITE}/pluginfile.php/1/slides.pptx")


def test_read_moodle_file_error(moodle):
    file_route(moodle, httpx.Response(200, json={"error": "File not found"}))
    with pytest.raises(MoodleError, match="File not found"):
        read_content(f"{SITE}/pluginfile.php/1/missing.pdf")


def test_read_page_activity(moodle):
    moodle.on("mod_page_get_pages_by_courses", {"pages": [
        {"coursemodule": 5, "name": "Useful links", "intro": "<p>Intro</p>", "content": "<p>Link list</p>"},
    ]})
    result = read_content(f"{SITE}/mod/page/view.php?id=5")
    assert result == {"name": "Useful links", "text": "Intro\n\nLink list", "total_chars": 16}


@pytest.mark.parametrize("url", [
    "https://evil.test/2026/pluginfile.php/1/x.pdf",          # other host: the token must never be sent there
    "https://moodle.test/2026.evil.test/pluginfile.php/1/x",  # prefix trick
    "https://moodle.test/2030/pluginfile.php/1/x.pdf",        # a year without a token
])
def test_read_refuses_foreign_urls(moodle, url):
    with pytest.raises(ValueError, match="Only links to your Moodle site"):
        read_content(url)
    assert moodle.router.calls.call_count == 0


def test_read_refuses_other_moodle_pages(moodle):
    with pytest.raises(ValueError, match="Pass a file url"):
        read_content(f"{SITE}/course/view.php?id=1")
