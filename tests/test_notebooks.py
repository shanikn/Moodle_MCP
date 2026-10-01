import pytest

from moodle_mcp import notebooks, runi
from tests.conftest import FIXTURES

FORM = (FIXTURES / "yedion_query_form.html").read_text(encoding="utf-8").replace('name="QueryCode" value="3"', 'name="QueryCode" value="482"')
NOTEBOOKS = (FIXTURES / "yedion_notebooks.html").read_text(encoding="utf-8")


def test_parse_notebooks():
    assert notebooks.parse_notebooks(NOTEBOOKS) == [
        {"course": "מבוא למדעי המחשב", "course_number": "100", "lecturer": 'ד"ר כהן משה', "type": "מבחן סופי",
         "moed": 1, "grade": 88, "appeal_deadline": "2026-02-18", "appeal": "deadline passed",
         "confidential": False, "files": ["exam_paper", "notebook"]},
        {"course": "אלגוריתמים", "course_number": "200", "lecturer": "פרופ' לוי דנה", "type": "מבחן סופי",
         "moed": 2, "grade": None, "appeal_deadline": None, "appeal": "no grade yet",
         "confidential": False, "files": []},
        {"course": "אלגוריתמים", "course_number": "200", "lecturer": "פרופ' לוי דנה", "type": "מבחן סופי - Campus",
         "moed": "special", "grade": 91.5, "appeal_deadline": "2026-06-18", "appeal": "confidential exam",
         "confidential": True, "files": []},
        {"course": "מערכות הפעלה", "course_number": "300", "lecturer": "מר אברהם יוסי", "type": "מבחן סופי",
         "moed": 1, "grade": 74, "appeal_deadline": "2026-10-30", "appeal": "open",
         "confidential": False, "files": ["answer_key", "notebook"]},
    ]


def test_results_never_carry_button_arguments():
    result = str(notebooks.parse_notebooks(NOTEBOOKS))
    assert "NoteBooks_Open_Do" not in result and "a1b2c3d4" not in result and "10001" not in result


def test_no_data_page_is_an_empty_list():
    assert notebooks.parse_notebooks('<b id="ExitStudent">x</b><div> אין נתונים בטווח שנבחר <br></div>') == []


def test_unexpected_page_is_an_error():
    with pytest.raises(runi.RuniError, match="no results table"):
        notebooks.parse_notebooks('<b id="ExitStudent">something else</b>')


def test_exam_notebooks_submits_the_query_form(runi_site):
    runi_site.pages = {"MenuCall": FORM, "StudentQueryExecution": NOTEBOOKS}
    assert len(notebooks.exam_notebooks(2026, 2)) == 4
    menu, submit = runi_site.posts
    assert (menu["PRGNAME"], menu["ARGUMENTS"]) == ("MenuCall", "-N,-N,-N482,-A")
    assert (submit["PRGNAME"], submit["QueryCode"], submit["R1C1"], submit["R1C2"]) == ("StudentQueryExecution", "482", "2026", "2")


def test_exam_notebooks_defaults_to_current_year_whole_year(runi_site, monkeypatch):
    monkeypatch.setattr(notebooks, "current_academic_year", lambda: 2027)
    runi_site.pages = {"MenuCall": FORM, "StudentQueryExecution": NOTEBOOKS}
    notebooks.exam_notebooks()
    assert (runi_site.posts[1]["R1C1"], runi_site.posts[1]["R1C2"]) == ("2027", "0")


def test_never_clicks_anything(runi_site):
    runi_site.pages = {"MenuCall": FORM, "StudentQueryExecution": NOTEBOOKS}
    notebooks.exam_notebooks(2026)
    assert [p["PRGNAME"] for p in runi_site.posts] == ["MenuCall", "StudentQueryExecution"]
