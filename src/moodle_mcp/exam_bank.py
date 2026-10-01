# past exams (בנק בחינות) from Yedion
import html
import re

from moodle_mcp import runi
from moodle_mcp.yedion_files import button_arguments, hidden_fields
from moodle_mcp.yedion_forms import grids, options, text

# menu item "בנק בחינות": a search form whose "חיפוש" button posts ExamBank with arguments that
# list the form fields (and embed the student's id and page token, so they are read from the page)
BANK_MENU = ("MenuCall", "-N,-N,-N73,-A")
NO_RESULTS = "לא נמצאו נתונים"
LANGUAGES = {"all": "A", "hebrew": "H", "english": "E"}


def _search_arguments(page: str) -> str:
    for args in re.findall(r'data-progname="ExamBank" data-arguments="([^"]*)"', page):
        if "R1C11" in args:  # the search button; the other ExamBank button clears the form
            return html.unescape(args)
    raise runi.RuniError("Yedion's exam bank page has no search button; the page layout may have changed.")


def _lecturer_code(page: str, lecturer: str) -> str:
    """Lecturer name (or part of it) -> the code Yedion's lecturer list uses."""
    block = re.search(r'(?s)<select[^>]*name="InnerTeacherCode".*?</select>', page)
    entries = [(v, text(t).replace("‏", "").strip())
               for v, t in re.findall(r'(?s)<option[^>]*value="?(\d+)"?[^>]*>(.*?)</option>', block.group() if block else "")]
    wanted = lecturer.strip().casefold()
    exact = [(v, t) for v, t in entries if t.casefold() == wanted]
    matches = exact or [(v, t) for v, t in entries if wanted in t.casefold()]
    if not matches:
        raise ValueError(f"No lecturer matching {lecturer!r} in Yedion's exam bank.")
    if len({t for _, t in matches}) > 1:
        names = sorted({t for _, t in matches})
        raise ValueError(f"{len(names)} lecturers match {lecturer!r}: {', '.join(names[:10])}. Give a fuller name.")
    return matches[0][0]


def _course_number(page: str, course: str) -> str:
    """Course number, or a name (or part of it) resolved against the bank's course list, whose
    entries read "מבוא להסתברות (109)". Yedion's own name search silently ignores a name it
    can't match, so names are resolved here."""
    block = re.search(r'(?s)<select[^>]*name="R1C1".*?</select>', page)
    entries = [(v, re.sub(r"\s*\(\d+\)$", "", text(t)))
               for v, t in re.findall(r'(?s)<option[^>]*value="?(\d+)"?[^>]*>(.*?)</option>', block.group() if block else "")]
    if course.isdigit():
        if course not in {v for v, _ in entries}:
            raise ValueError(f"Course number {course} is not in Yedion's exam bank.")
        return course
    wanted = course.casefold()
    exact = {v: t for v, t in entries if t.casefold() == wanted}
    matches = exact or {v: t for v, t in entries if wanted in t.casefold()}
    if not matches:
        raise ValueError(f"No course matching {course!r} in Yedion's exam bank.")
    if len(matches) > 1:
        listed = ", ".join(f"{t} ({v})" for v, t in list(matches.items())[:15])
        raise ValueError(f"{len(matches)} courses match {course!r}: {listed}. Pass the course number.")
    return next(iter(matches))


def _number_or_text(value: str):
    return int(value) if value.isdigit() else value or None


def _rows(page: str) -> list[dict[str, str]]:
    """Result rows ("סימון | בית ספר | קוד קורס | קורס | ... | קובץ") with each cell's HTML."""
    results = next((rows for header, rows in grids(page, raw=True) if "קוד קורס" in header and "מועד" in header), None)
    if results is None:
        if NO_RESULTS in page:
            return []
        raise runi.RuniError("Yedion's exam bank page has no results table; the page layout may have changed.")
    return results


def _parse_row(row: dict[str, str]) -> dict:
    cell = {key: text(value) for key, value in row.items()}
    year = re.search(r"\((\d{4})\)", cell.get("שנה", ""))  # 'תשפ"ה (2025)'
    return {
        "course": cell.get("קורס"),
        "course_number": cell.get("קוד קורס"),
        "school": cell.get("בית ספר") or None,
        "type": cell.get("סוג מקצוע") or None,
        "year": int(year.group(1)) if year else None,
        "semester": _number_or_text(cell.get("סמסטר", "")),
        "moed": _number_or_text(cell.get("מועד", "")),
        "lecturer": cell.get("מרצה") or None,
    }


def _sort_key(exam: dict):
    return (-(exam["year"] or 0), str(exam["semester"]), str(exam["moed"]))


def parse_results(page: str) -> list[dict]:
    return sorted((_parse_row(row) for row in _rows(page)), key=_sort_key)


def _search(course: str, lecturer: str | None, year: int | None, semester: int | None, language: str) -> str:
    """Run a search and return the results page (two requests)."""
    course = course.strip()
    if not course:
        raise ValueError("Give a course name (or part of it) or a course number.")
    if language not in LANGUAGES:
        raise ValueError(f"language must be one of {', '.join(LANGUAGES)}.")
    page = runi.fetch(*BANK_MENU)
    fields = {"R1C1": "", "R1C11": "", "InnerTeacherCode": "", "R1C3": LANGUAGES[language],
              "R1C4": "", "R1C5": "0", "R1C13": ""}
    fields["R1C1"] = _course_number(page, course)
    if lecturer:
        fields["InnerTeacherCode"] = _lecturer_code(page, lecturer)
    if year is not None:
        years = options(page, "R1C4")
        if str(year) not in years:
            raise ValueError(f"The exam bank has no year {year}. Available years: {', '.join(years[:12])}, ...")
        fields["R1C4"] = str(year)
    if semester:
        if str(semester) not in options(page, "R1C5"):
            raise ValueError(f"Invalid semester {semester}: use 1, 2, ... or omit it for all semesters.")
        fields["R1C5"] = str(semester)
    return runi.fetch("ExamBank", _search_arguments(page), **fields)


def search_exam_bank(course: str, lecturer: str | None = None, year: int | None = None,
                     semester: int | None = None, language: str = "all") -> list[dict]:
    return parse_results(_search(course, lecturer, year, semester, language))


def open_file(course: str, year: int, semester: int, moed: int | str, lecturer: str | None = None) -> tuple[dict, bytes]:
    """Find one past exam and download its file (the "הורדה" button). Returns (exam, pdf)."""
    page = _search(course, lecturer, year, semester, "all")
    matches = [(row, exam) for row in _rows(page) for exam in [_parse_row(row)]
               if exam["moed"] == moed and exam["year"] == year and exam["semester"] == semester]
    if not matches:
        raise ValueError(f"No exam bank file for {course}, {year} semester {semester}, moed {moed}. "
                         "List them with search_exam_bank.")
    distinct = {(exam["lecturer"], exam["school"]) for _, exam in matches}
    if len({lecturer_ for lecturer_, _ in distinct}) > 1:
        names = sorted({lecturer_ or "?" for lecturer_, _ in distinct})
        raise ValueError(f"{len(names)} exams match ({', '.join(names)}): pass the lecturer.")
    row, exam = matches[0]  # same lecturer: the same exam listed once per school
    arguments = button_arguments(row.get("קובץ", ""), "ExamBank", kind="-N10")
    if arguments is None:
        raise ValueError("This exam bank entry has no file to download.")
    return exam, runi.fetch_file("ExamBank", arguments, **hidden_fields(page))
