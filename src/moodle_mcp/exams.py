# the student's exam schedule (לוח בחינות) from Yedion
import re
from datetime import datetime

from moodle_mcp import runi
from moodle_mcp.yedion_forms import current_academic_year, hidden, options, text

# menu item "לוח בחינות" opens a form (year R1C1, semester R1C2, moed Terms); "ביצוע" submits it
FORM = ("MenuCall", "-N,-N,-N6,-A")
SUBMIT = ("HADPASAT_TOCHNIT_BEHINOT", "TZ,Token,R1C1,R1C2,R1C3")
ROOM_NOT_SET = "טרם נקבע"
SPECIAL_MOED = "מועד מיוחד"
NO_EXAMS = "אין מידע ליצירת תוכנית בחינות"  # shown instead of the grid when nothing matches


def _date(value: str) -> str | None:
    """"30/01/2026" -> "2026-01-30"; empty -> None."""
    return datetime.strptime(value, "%d/%m/%Y").strftime("%Y-%m-%d") if value else None


def _number_or_text(value: str):
    return int(value) if value.isdigit() else value


def _registered(status: str) -> bool | None:
    """"רשומה למבחן" / "רשום למבחן" -> True, "לא רשומה למבחן" -> False, anything else -> None."""
    if status.startswith("לא "):
        return False
    return True if "רשומ" in status or "רשום" in status else None


def parse_exams(page: str, semester: int | None = None) -> list[dict]:
    """Rows of the results grid (div.row / div.col, the first row is the header).

    Columns are looked up by header text: the semester column is only there when the whole
    year was requested, so `semester` fills it in otherwise."""
    start = page.find('class="PrintAsBox Table')
    if start < 0 and NO_EXAMS in page:
        return []
    if start < 0:
        raise runi.RuniError("Yedion's exam schedule page has no results table; the page layout may have changed.")
    rows = [[text(cell) for cell in re.findall(r'(?s)<div class="col[^"]*">(.*?)</div>', row)]
            for row in re.split(r'<div class="row[^"]*">', page[start:])[1:]]
    header = rows[0] if rows else []
    if "קוד קורס" not in header or "תאריך" not in header:
        raise runi.RuniError("Yedion's exam schedule table has unexpected columns; the page layout may have changed.")

    exams = []
    for cells in rows[1:]:
        if len(cells) != len(header):  # e.g. the footer links after the grid
            continue
        row = dict(zip(header, cells))
        moed = row.get("מועד", "")
        room = row.get("חדר בחינה", "")
        alternative = row.get("הערכה חלופית", "")
        exams.append({
            "course": row["שם קורס"],
            "course_number": row["קוד קורס"],
            "lecturer": row.get("שם המרצה") or None,
            "semester": _number_or_text(row["סמסטר"]) if "סמסטר" in row else semester,
            "moed": "special" if moed == SPECIAL_MOED else _number_or_text(moed),
            "type": row.get("סוג מקצוע") or None,
            "date": _date(row["תאריך"]),
            "start": row.get("שעת התחלה") or None,
            "room": None if room in ("", ROOM_NOT_SET) else room,
            "registered": _registered(row.get("סטטוס רישום", "")),
            "appeal_deadline": _date(row.get("תאריך אחרון להגשת ערעור", "")),
            "alternative_assessment": alternative or None,
        })
    return sorted(exams, key=lambda e: (e["date"] or "9999", e["start"] or ""))


def exam_schedule(year: int | None = None, semester: int | None = None) -> list[dict]:
    year = current_academic_year() if year is None else year
    form = runi.fetch(*FORM)
    years = options(form, "R1C1")
    if str(year) not in years:
        raise ValueError(f"Yedion has no exam schedule for {year}. Available years: {', '.join(years)}.")
    semesters = options(form, "R1C2")
    if str(semester or 0) not in semesters:
        raise ValueError(f"Invalid semester {semester}: use one of {', '.join(semesters)} (0 = the whole year).")
    page = runi.fetch(*SUBMIT, TZ=hidden(form, "TZ"), Token=hidden(form, "Token"),
                      R1C1=str(year), R1C2=str(semester or 0), Terms="0")
    return parse_exams(page, semester)
