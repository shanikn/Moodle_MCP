# the student's exam notebooks (מחברות בחינה) from Yedion: per exam the grade and which files
# (exam paper / solution, multiple-choice key, scanned notebook) can be opened. Files are not
# opened here; the buttons' arguments embed the student id and page token and stay internal.
import re
from datetime import datetime

from moodle_mcp import runi
from moodle_mcp.yedion_forms import NO_DATA, current_academic_year, grids, run_query, text

NOTEBOOKS_MENU = 482
SPECIAL_MOED = "מועד מיוחד"
CONFIDENTIAL = "בחינה חסויה"
PAPER, ANSWER_KEY, NOTEBOOK, APPEAL = "שאלון / פתרון בחינה", "תשובון רב ברירה", "מחברת בחינה", "הגשת ערעור"


def _date(value: str) -> str | None:
    return datetime.strptime(value, "%d/%m/%Y").strftime("%Y-%m-%d") if value else None


def _grade(value: str):
    """"87" -> 87, "87.5" -> 87.5, "טרם" (not graded yet) -> None, other text (e.g. "עבר") as is."""
    if re.fullmatch(r"\d+", value):
        return int(value)
    if re.fullmatch(r"\d+\.\d+", value):
        return float(value)
    return None if not value or value.startswith("טרם") else value


def _appeal(cell: str) -> str:
    """The appeal column as a status. An open appeal is a button; this tool never submits one."""
    note = text(cell)
    if "<button" in cell:
        return "open"
    if "טרם" in note:
        return "no grade yet"
    if "חסויה" in note:
        return "confidential exam"
    if "עבר" in note:  # "תאריך אחרון של ערעור עבר"
        return "deadline passed"
    return note or "not available"


def parse_notebooks(page: str) -> list[dict]:
    found = next((rows for header, rows in grids(page, raw=True) if "נושא" in header and "מועד" in header), None)
    if found is None:
        if NO_DATA in page:
            return []
        raise runi.RuniError("Yedion's exam notebooks page has no results table; the page layout may have changed.")
    exams = []
    for row in found:
        number, _, name = text(row["נושא"]).partition(" ")  # "79 ארכיטקטורות דיגיטליות"
        moed = text(row.get("מועד", ""))
        files = {key: "<button" in row.get(column, "") for key, column in
                 (("exam_paper", PAPER), ("answer_key", ANSWER_KEY), ("notebook", NOTEBOOK))}
        exams.append({
            "course": name.strip() if number.isdigit() else text(row["נושא"]),
            "course_number": number if number.isdigit() else None,
            "lecturer": text(row.get("שם מרצה", "")) or None,
            "type": text(row.get("סוג מקצוע", "")) or None,
            "moed": "special" if moed == SPECIAL_MOED else int(moed) if moed.isdigit() else moed or None,
            "grade": _grade(text(row.get("הציון", ""))),
            "appeal_deadline": _date(text(row.get("תאריך אחרון לערעור", ""))),
            "appeal": _appeal(row.get(APPEAL, "")),
            "confidential": any(CONFIDENTIAL in text(cell) for cell in row.values()),
            "files": [key for key, available in files.items() if available],
        })
    return exams


def exam_notebooks(year: int | None = None, semester: int | None = None) -> list[dict]:
    year = current_academic_year() if year is None else year
    return parse_notebooks(run_query(NOTEBOOKS_MENU, year, semester or 0))
