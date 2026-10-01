import re
from datetime import date

import pytest

from moodle_mcp import exams, runi
from tests.conftest import FIXTURES

FORM = (FIXTURES / "yedion_exam_form.html").read_text(encoding="utf-8")
RESULTS = (FIXTURES / "yedion_exams.html").read_text(encoding="utf-8")
NO_EXAMS = (FIXTURES / "yedion_no_exams.html").read_text(encoding="utf-8")


def test_parse_exams_sorted_by_date():
    assert exams.parse_exams(RESULTS) == [
        {"course": "מבוא למדעי המחשב", "course_number": "100", "lecturer": 'ד"ר כהן משה', "semester": 1,
         "moed": 1, "type": "מבחן סופי", "date": "2026-01-30", "start": "09:00",
         "room": "מיקום הבחינה יפורסם כשעה לפני הבחינה", "registered": True,
         "appeal_deadline": "2026-02-18", "alternative_assessment": None},
        {"course": "פרויקט גמר", "course_number": "300", "lecturer": "מר אברהם יוסי", "semester": 1,
         "moed": 1, "type": "עבודה", "date": "2026-02-15", "start": None, "room": None, "registered": None,
         "appeal_deadline": None, "alternative_assessment": "עבודה מסכמת"},
        {"course": "אלגוריתמים", "course_number": "200", "lecturer": "פרופ' לוי דנה", "semester": 2,
         "moed": "special", "type": "מבחן סופי - Campus", "date": "2026-08-05", "start": "17:30",
         "room": None, "registered": False, "appeal_deadline": None, "alternative_assessment": None},
    ]


def test_parse_exams_without_semester_column_uses_the_requested_semester():
    # Yedion shows the semester column only for the whole year
    page = re.sub(r'(<div class="row ?">\s*)<div class="col col-Small">[^<]*</div>', r"\1", RESULTS)
    rows = exams.parse_exams(page, semester=1)
    assert [r["course_number"] for r in rows] == ["100", "300", "200"]
    assert {r["semester"] for r in rows} == {1}


def test_no_exams_page_is_an_empty_list():
    assert exams.parse_exams(NO_EXAMS) == []


def test_unexpected_page_is_an_error():
    with pytest.raises(runi.RuniError, match="no results table"):
        exams.parse_exams('<b id="ExitStudent">something else</b>')


def test_exam_schedule_submits_the_form(runi_site):
    runi_site.pages = {"MenuCall": FORM, "HADPASAT_TOCHNIT_BEHINOT": RESULTS}
    result = exams.exam_schedule(2027, 2)
    assert [r["course_number"] for r in result] == ["100", "300", "200"]
    menu, submit = runi_site.posts
    assert (menu["PRGNAME"], menu["ARGUMENTS"]) == ("MenuCall", "-N,-N,-N6,-A")
    assert submit == {"PRGNAME": "HADPASAT_TOCHNIT_BEHINOT", "ARGUMENTS": "TZ,Token,R1C1,R1C2,R1C3",
                      "TZ": "000000018", "Token": "00000000-test-page-token",
                      "R1C1": "2027", "R1C2": "2", "Terms": "0"}


@pytest.mark.parametrize("today, year", [
    (date(2026, 9, 30), 2026), (date(2026, 10, 1), 2027), (date(2027, 1, 15), 2027), (date(2027, 9, 30), 2027),
])
def test_current_academic_year(today, year):
    assert exams.current_academic_year(today) == year


def test_exam_schedule_defaults_to_current_year_whole_year(runi_site, monkeypatch):
    monkeypatch.setattr(exams, "current_academic_year", lambda: 2026)
    runi_site.pages = {"MenuCall": FORM, "HADPASAT_TOCHNIT_BEHINOT": NO_EXAMS}
    assert exams.exam_schedule() == []
    assert (runi_site.posts[1]["R1C1"], runi_site.posts[1]["R1C2"]) == ("2026", "0")


@pytest.mark.parametrize("year, semester, message", [
    (2030, None, "no exam schedule for 2030. Available years: 2027, 2026, 2025"),
    (2026, 7, "Invalid semester 7: use one of 0, 1, 2, 3"),
])
def test_bad_year_or_semester(runi_site, year, semester, message):
    runi_site.pages = {"MenuCall": FORM}
    with pytest.raises(ValueError, match=message):
        exams.exam_schedule(year, semester)
    assert len(runi_site.posts) == 1  # nothing submitted
