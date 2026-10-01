import pytest

from moodle_mcp import runi, schedule
from moodle_mcp.yedion_forms import grids
from tests.conftest import FIXTURES

FORM = (FIXTURES / "yedion_query_form.html").read_text(encoding="utf-8")
TIMETABLE = (FIXTURES / "yedion_timetable.html").read_text(encoding="utf-8")
NO_DATA = ('<b id="ExitStudent">x</b><h2 class="TextAlignCenter"></h2>'
           '<div style="margin:auto;" class="TextAlign Width100"> אין נתונים בטווח שנבחר <br></div>')


def test_parse_schedule():
    result = schedule.parse_schedule(TIMETABLE)
    assert result["total_credits"] == 8.0 and result["total_weekly_hours"] == 8.0
    assert result["courses"] == [
        {"course": "מבוא למדעי המחשב", "course_number": "100", "semester": 1, "type": "שיעור", "group": None,
         "lecturer": 'ד"ר כהן משה', "credits": 4.0, "weekly_hours": 4.0,
         "meetings": [{"day": "Monday", "start": "08:45", "end": "11:15"}], "room": "SL301", "notes": []},
        {"course": "מבוא למדעי המחשב", "course_number": "100", "semester": 1, "type": "תרגול", "group": 4,
         "lecturer": "מר כהן משה", "credits": None, "weekly_hours": 1.0,
         "meetings": [{"day": "Thursday", "start": "09:45", "end": "10:45"}], "room": "C.B02", "notes": ["קבוצה 4"]},
        {"course": "ללמוד איך ללמוד", "course_number": "400", "semester": 1, "type": "מכינה", "group": None,
         "lecturer": None, "credits": None, "weekly_hours": None, "meetings": [], "room": None, "notes": ["קורס מקוון"]},
        {"course": "גרפיקה ממוחשבת", "course_number": "300", "semester": 2, "type": "שיעור", "group": None,
         "lecturer": "פרופ' לוי דנה", "credits": 4.0, "weekly_hours": 3.0,
         "meetings": [{"day": "Tuesday", "start": "15:45", "end": "18:15"}], "room": "L101 אודיטוריום", "notes": []},
    ]


def test_grids_are_bounded_per_card_and_skip_the_student_block_and_footer():
    headers = [h for h, _ in grids(TIMETABLE)]
    assert headers[1:] == [["בית ספר", "סך הכל נקודות זכות", 'סך הכל ש"ס'], ["קוד הערה", "מלל הערה"]]
    assert all("000000018" not in str(rows) for _, rows in grids(TIMETABLE))


def test_no_data_page_is_an_empty_schedule():
    assert schedule.parse_schedule(NO_DATA) == {"courses": [], "total_credits": 0.0, "total_weekly_hours": 0.0}


def test_unexpected_page_is_an_error():
    with pytest.raises(runi.RuniError, match="no results table"):
        schedule.parse_schedule('<b id="ExitStudent">something else</b>')


def test_class_schedule_submits_the_query_form(runi_site):
    runi_site.pages = {"MenuCall": FORM, "StudentQueryExecution": TIMETABLE}
    result = schedule.class_schedule(2027, 1)
    assert len(result["courses"]) == 4
    menu, submit = runi_site.posts
    assert (menu["PRGNAME"], menu["ARGUMENTS"]) == ("MenuCall", "-N,-N,-N3,-A")
    assert submit == {"PRGNAME": "StudentQueryExecution", "ARGUMENTS": "TZ,Token,QueryCode,R1C1,R1C2",
                      "TZ": "000000018", "Token": "00000000-test-page-token", "QueryCode": "3",
                      "R1C1": "2027", "R1C2": "1"}


def test_class_schedule_defaults_to_current_year_whole_year(runi_site, monkeypatch):
    monkeypatch.setattr(schedule, "current_academic_year", lambda: 2026)
    runi_site.pages = {"MenuCall": FORM, "StudentQueryExecution": NO_DATA}
    schedule.class_schedule()
    assert (runi_site.posts[1]["R1C1"], runi_site.posts[1]["R1C2"]) == ("2026", "0")


@pytest.mark.parametrize("year, semester, message", [
    (2030, None, "no data for 2030. Available years: 2027, 2026, 2025"),
    (2026, 7, "Invalid semester 7: use one of 0, 1, 2, 3"),
])
def test_bad_year_or_semester(runi_site, year, semester, message):
    runi_site.pages = {"MenuCall": FORM}
    with pytest.raises(ValueError, match=message):
        schedule.class_schedule(year, semester)
    assert len(runi_site.posts) == 1  # nothing submitted
