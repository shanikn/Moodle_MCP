import asyncio
import builtins
import io
import json
import os
import tempfile

import pytest
from PIL import Image as PILImage

from moodle_mcp import exam_bank, notebooks, runi, yedion_files
from moodle_mcp.server import mcp
from tests.conftest import FIXTURES, make_pdf

FORM = (FIXTURES / "yedion_query_form.html").read_text(encoding="utf-8").replace('value="3"', 'value="482"')
NOTEBOOKS = (FIXTURES / "yedion_notebooks.html").read_text(encoding="utf-8")
BANK = (FIXTURES / "yedion_exam_bank.html").read_text(encoding="utf-8")
PDF = make_pdf(["Cover page"] + [None] * 11)  # 12 pages, text only on page 1


# --- rendering -------------------------------------------------------------------------------

def test_first_call_returns_up_to_10_pages_as_jpeg_with_the_text_layer():
    info, images = yedion_files.render_pages(PDF)
    assert info == {"pages_total": 12, "pages": [1, 10], "text": {"1": "Cover page"}, "next_first_page": 11}
    assert len(images) == 10 and all(image[:2] == b"\xff\xd8" for image in images)  # JPEG
    assert max(PILImage.open(io.BytesIO(images[0])).size) == yedion_files.LONG_EDGE


def test_page_range_is_clamped_to_the_end_of_the_file():
    info, images = yedion_files.render_pages(PDF, first_page=11, last_page=40)
    assert info == {"pages_total": 12, "pages": [11, 12], "text": {}}
    assert len(images) == 2


@pytest.mark.parametrize("first, last, message", [
    (1, 11, "At most 10 pages per call"),
    (13, None, "between 1 and 12"),
    (0, None, "between 1 and 12"),
    (5, 4, "at least first_page"),
])
def test_bad_page_ranges(first, last, message):
    with pytest.raises(ValueError, match=message):
        yedion_files.render_pages(PDF, first, last)


def test_a_broken_pdf_is_a_clear_error():
    with pytest.raises(ValueError, match="could not be read as a PDF"):
        yedion_files.render_pages(b"%PDF-1.4 truncated")


def test_nothing_is_written_to_disk(monkeypatch, runi_site):
    def refuse(*args, **kwargs):
        raise AssertionError("tried to write a file")

    real_open = builtins.open

    def open_read_only(file, mode="r", *args, **kwargs):
        if any(flag in mode for flag in "wax+"):
            refuse()
        return real_open(file, mode, *args, **kwargs)

    runi_site.pages = {"MenuCall": FORM, "StudentQueryExecution": NOTEBOOKS, "NoteBooks_Open_Do": PDF}
    monkeypatch.setattr(builtins, "open", open_read_only)
    for name in ("NamedTemporaryFile", "TemporaryFile", "mkstemp", "mkdtemp", "TemporaryDirectory"):
        monkeypatch.setattr(tempfile, name, refuse)
    monkeypatch.setattr(os, "open", refuse)
    exam, pdf = notebooks.open_file("100", 1, "notebook", 2026)
    info, images = yedion_files.render_pages(pdf)
    assert info["pages_total"] == 12 and len(images) == 10


# --- exam notebooks --------------------------------------------------------------------------

def test_notebook_file_posts_the_button_with_the_page_form_fields(runi_site):
    runi_site.pages = {"MenuCall": FORM, "StudentQueryExecution": NOTEBOOKS, "NoteBooks_Open_Do": PDF}
    exam, pdf = notebooks.open_file("100", 1, "exam_paper", 2026, 1)
    assert pdf == PDF and exam["course"] == "מבוא למדעי המחשב"
    download = runi_site.posts[-1]
    assert download == {"PRGNAME": "NoteBooks_Open_Do", "TZ": "000000018", "Token": "00000000-test-page-token",
                        "ARGUMENTS": "TZ,Token,-AH,-N2026,-N1,-N10001,-N,-N100,-N6,-N1,-AT,-AM,-N10002,0a1b2c3d4e5f60718293a4b5c6d7e8f9"}


def test_confidential_exam_is_reported_and_never_fetched(runi_site):
    runi_site.pages = {"MenuCall": FORM, "StudentQueryExecution": NOTEBOOKS}
    exam, pdf = notebooks.open_file("200", "special", "exam_paper", 2026)
    assert pdf is None and exam["confidential"] is True
    assert "NoteBooks_Open_Do" not in [p["PRGNAME"] for p in runi_site.posts]


@pytest.mark.parametrize("args, message", [
    (("100", 1, "answer_key"), "no answer_key to open; available: exam_paper, notebook"),
    (("200", 2, "notebook"), "no notebook to open; available: none"),
    (("999", 1, "notebook"), "No exam of course 999, moed 1 in 2026"),
    (("100", 1, "everything"), "file must be one of exam_paper, answer_key, notebook"),
])
def test_notebook_file_errors(runi_site, args, message):
    runi_site.pages = {"MenuCall": FORM, "StudentQueryExecution": NOTEBOOKS}
    with pytest.raises(ValueError, match=message):
        notebooks.open_file(*args, year=2026)
    assert "NoteBooks_Open_Do" not in [p["PRGNAME"] for p in runi_site.posts]


def test_a_non_pdf_answer_is_an_error(runi_site):
    runi_site.pages = {"MenuCall": FORM, "StudentQueryExecution": NOTEBOOKS,
                       "NoteBooks_Open_Do": '<b id="ExitStudent">an error page</b>'}
    with pytest.raises(runi.RuniError, match="did not return a PDF file"):
        notebooks.open_file("100", 1, "notebook", 2026)


# --- exam bank -------------------------------------------------------------------------------

def test_exam_bank_file_uses_the_download_button(runi_site):
    runi_site.pages = {"MenuCall": BANK, "ExamBank": BANK}
    real_post = runi_site.firefly_post

    def answer(request):  # the search and the download are both ExamBank posts
        response = real_post(request)
        if runi_site.posts[-1]["ARGUMENTS"].split(",")[2] == "-N10":
            return type(response)(200, content=PDF, headers={"Content-Type": "Application/pdf"})
        return response

    runi_site.router.routes[-1].side_effect = answer
    exam, pdf = exam_bank.open_file("109", 2026, 1, 2)
    assert pdf == PDF and (exam["lecturer"], exam["moed"]) == ("כהן משה", 2)
    assert runi_site.posts[-1]["ARGUMENTS"] == "-N000000018,00000000-test-page-token,-N10,-A,-N109,-N0,-A,-N2026,-N1,-N10002,-N,-N6,-N2"


def test_exam_bank_file_not_found(runi_site):
    runi_site.pages = {"MenuCall": BANK, "ExamBank": BANK}
    with pytest.raises(ValueError, match="No exam bank file for 109, 2025 semester 1, moed 1"):
        exam_bank.open_file("109", 2025, 1, 1)


def test_exam_bank_file_needs_the_lecturer_when_several_match(runi_site):
    two = BANK.replace("<div class=\"col\">2</div><div class=\"col\">1</div><div class=\"col\">לוי דנה</div>",
                       "<div class=\"col\">1</div><div class=\"col\">1</div><div class=\"col\">לוי דנה</div>")
    two = two.replace("תשע\"ו (2016)", "תשפ\"ו (2026)")
    runi_site.pages = {"MenuCall": BANK, "ExamBank": two}
    with pytest.raises(ValueError, match="2 exams match .*pass the lecturer"):
        exam_bank.open_file("109", 2026, 1, 1)


# --- tools -----------------------------------------------------------------------------------

def call_tool(name, args):
    return asyncio.run(mcp.call_tool(name, args))


def test_file_tool_returns_json_then_one_image_per_page(runi_site):
    runi_site.pages = {"MenuCall": FORM, "StudentQueryExecution": NOTEBOOKS, "NoteBooks_Open_Do": PDF}
    result = call_tool("read_exam_notebook_file", {"course_number": "100", "moed": 1, "file": "notebook",
                                                   "year": 2026, "first_page": 3, "last_page": 4})
    summary = json.loads(result.content[0].text)
    assert summary["pages"] == [3, 4] and summary["pages_total"] == 12 and summary["exam"]["course_number"] == "100"
    assert [block.type for block in result.content[1:]] == ["image", "image"]
    assert result.content[1].mime_type == "image/jpeg"
    assert "000000018" not in result.content[0].text and "test-page-token" not in result.content[0].text


def test_file_tool_reports_a_confidential_exam_without_images(runi_site):
    runi_site.pages = {"MenuCall": FORM, "StudentQueryExecution": NOTEBOOKS}
    result = call_tool("read_exam_notebook_file", {"course_number": "200", "moed": "special",
                                                   "file": "exam_paper", "year": 2026})
    assert len(result.content) == 1
    assert "Confidential exam" in json.loads(result.content[0].text)["message"]
