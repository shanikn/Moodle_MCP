# past exams (בנק בחינות) from Yedion
import html
import re

from moodle_mcp import runi
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


def parse_results(page: str) -> list[dict]:
    """Rows of the results grid ("סימון | בית ספר | קוד קורס | קורס | ... | קובץ")."""
    results = next((rows for header, rows in grids(page) if "קוד קורס" in header and "מועד" in header), None)
    if results is None:
        if NO_RESULTS in page:
            return []
        raise runi.RuniError("Yedion's exam bank page has no results table; the page layout may have changed.")
    exams = []
    for row in results:
        year = re.search(r"\((\d{4})\)", row.get("שנה", ""))  # 'תשפ"ה (2025)'
        exams.append({
            "course": row.get("קורס"),
            "course_number": row.get("קוד קורס"),
            "school": row.get("בית ספר") or None,
            "type": row.get("סוג מקצוע") or None,
            "year": int(year.group(1)) if year else None,
            "semester": _number_or_text(row.get("סמסטר", "")),
            "moed": _number_or_text(row.get("מועד", "")),
            "lecturer": row.get("מרצה") or None,
        })
    return sorted(exams, key=lambda e: (-(e["year"] or 0), str(e["semester"]), str(e["moed"])))


def search_exam_bank(course: str, lecturer: str | None = None, year: int | None = None,
                     semester: int | None = None, language: str = "all") -> list[dict]:
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
    return parse_results(runi.fetch("ExamBank", _search_arguments(page), **fields))
