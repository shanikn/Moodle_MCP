import pytest

from moodle_mcp import exam_bank, runi
from tests.conftest import FIXTURES

BANK = (FIXTURES / "yedion_exam_bank.html").read_text(encoding="utf-8")
NO_RESULTS = BANK[:BANK.index("<div class=\"card g-brd-primary rounded-0 ShowMeAlways searchWrapper MasterTable\"><h2 class=\"card-header-H2\">תוצאות")] + \
    '<h2>תוצאות חיפוש</h2><div class="TextAlign">לא נמצאו נתונים</div></form></article></main></body></html>'


def search(runi_site, page=BANK, **kwargs):
    runi_site.pages = {"MenuCall": BANK, "ExamBank": page}
    return exam_bank.search_exam_bank(**kwargs)


def test_parse_results_newest_first():
    assert exam_bank.parse_results(BANK) == [
        {"course": "מבוא להסתברות", "course_number": "109", "school": "בית הספר למנהל עסקים .B.A", "type": "מבחן סופי",
         "year": 2026, "semester": 1, "moed": 1, "lecturer": "כהן משה"},
        {"course": "מבוא להסתברות", "course_number": "109", "school": "בית הספר למדעי המחשב .B.Sc", "type": "מבחן סופי",
         "year": 2026, "semester": 1, "moed": 2, "lecturer": "כהן משה"},
        {"course": "מבוא להסתברות", "course_number": "109", "school": "בית הספר למדעי המחשב .B.Sc", "type": "מבחן סופי",
         "year": 2016, "semester": 2, "moed": 1, "lecturer": "לוי דנה"},
    ]


def test_results_never_carry_the_id_or_page_token():
    assert "000000018" not in str(exam_bank.parse_results(BANK))
    assert "test-page-token" not in str(exam_bank.parse_results(BANK))


def test_no_results_is_an_empty_list():
    assert exam_bank.parse_results(NO_RESULTS) == []


def test_unexpected_page_is_an_error():
    with pytest.raises(runi.RuniError, match="no results table"):
        exam_bank.parse_results('<b id="ExitStudent">something else</b>')


def test_search_by_name_posts_the_course_number_and_the_page_arguments(runi_site):
    assert len(search(runi_site, course="מבוא להסתברות")) == 3
    menu, submit = runi_site.posts
    assert (menu["PRGNAME"], menu["ARGUMENTS"]) == ("MenuCall", "-N,-N,-N73,-A")
    assert submit == {"PRGNAME": "ExamBank",
                      "ARGUMENTS": "-N000000018,00000000-test-page-token,-N20,-A,R1C1,InnerTeacherCode,R1C3,R1C4,R1C5,,,,,,R1C11,R1C13",
                      "R1C1": "109", "R1C11": "", "InnerTeacherCode": "", "R1C3": "A", "R1C4": "", "R1C5": "0", "R1C13": ""}


def test_filters(runi_site):
    search(runi_site, course="109", lecturer="כהן", year=2026, semester=1, language="hebrew")
    submit = runi_site.posts[1]
    assert (submit["R1C1"], submit["InnerTeacherCode"], submit["R1C4"], submit["R1C5"], submit["R1C3"]) == \
        ("109", "6583", "2026", "1", "H")


def test_lecturer_exact_name_wins_over_partial_matches(runi_site):
    search(runi_site, course="109", lecturer="לוי דן")  # also a substring of "לוי דנה"
    assert runi_site.posts[1]["InnerTeacherCode"] == "6585"


@pytest.mark.parametrize("kwargs, message", [
    (dict(course="הסתברות"), r"2 courses match 'הסתברות': הסתברות \(8189\), הסתברות \(8054\). Pass the course number"),
    (dict(course="no such course"), "No course matching 'no such course'"),
    (dict(course="7777"), "Course number 7777 is not in Yedion's exam bank"),
    (dict(course="109", lecturer="לוי"), "2 lecturers match 'לוי'"),
    (dict(course="109", lecturer="nobody"), "No lecturer matching 'nobody'"),
    (dict(course="109", year=1990), "no year 1990. Available years: 2027, 2026, 2025"),
    (dict(course="109", semester=7), "Invalid semester 7"),
    (dict(course="109", language="french"), "language must be one of all, hebrew, english"),
    (dict(course="  "), "Give a course name"),
])
def test_bad_input_is_rejected_before_searching(runi_site, kwargs, message):
    with pytest.raises(ValueError, match=message):
        search(runi_site, **kwargs)
    assert [p["PRGNAME"] for p in runi_site.posts] in ([], ["MenuCall"])  # nothing searched
