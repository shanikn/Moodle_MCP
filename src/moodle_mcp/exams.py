# the student's exam schedule (לוח בחינות) from Yedion
import html
import re
from datetime import date, datetime

from moodle_mcp import runi

# menu item "לוח בחינות" opens a form (year R1C1, semester R1C2, moed Terms); "ביצוע" submits it
FORM = ("MenuCall", "-N,-N,-N6,-A")
SUBMIT = ("HADPASAT_TOCHNIT_BEHINOT", "TZ,Token,R1C1,R1C2,R1C3")
ROOM_NOT_SET = "טרם נקבע"
SPECIAL_MOED = "מועד מיוחד"
NO_EXAMS = "אין מידע ליצירת תוכנית בחינות"  # shown instead of the grid when nothing matches


def _text(fragment: str) -> str:
    """HTML cell -> plain text ("&nbsp;" and tags removed)."""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def _options(page: str, select: str) -> list[str]:
    """Numeric option values of a <select> (skips the disabled "choose..." placeholder)."""
    block = re.search(rf'(?s)<select[^>]*name="{select}".*?</select>', page)
    return re.findall(r'<option[^>]*value="?(\d+)"?', block.group()) if block else []


def _hidden(page: str, name: str) -> str:
    # these hold the student's id and a page token: keep them out of error messages
    match = re.search(rf'<input[^>]*name="{name}"[^>]*value="([^"]*)"', page)
    if not match:
        raise runi.RuniError(f"Yedion's exam schedule form is missing the {name} field; the page layout may have changed.")
    return match.group(1)


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
    rows = [[_text(cell) for cell in re.findall(r'(?s)<div class="col[^"]*">(.*?)</div>', row)]
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


def current_academic_year(today: date | None = None) -> int:
    """Academic years run October to September and are named by the year they end in:
    2026-10-01 .. 2027-09-30 is 2027 (תשפ"ז)."""
    today = today or date.today()
    return today.year + 1 if today.month >= 10 else today.year


def exam_schedule(year: int | None = None, semester: int | None = None) -> list[dict]:
    year = current_academic_year() if year is None else year
    form = runi.fetch(*FORM)
    years = _options(form, "R1C1")
    if str(year) not in years:
        raise ValueError(f"Yedion has no exam schedule for {year}. Available years: {', '.join(years)}.")
    semesters = _options(form, "R1C2")
    if str(semester or 0) not in semesters:
        raise ValueError(f"Invalid semester {semester}: use one of {', '.join(semesters)} (0 = the whole year).")
    page = runi.fetch(*SUBMIT, TZ=_hidden(form, "TZ"), Token=_hidden(form, "Token"),
                      R1C1=str(year), R1C2=str(semester or 0), Terms="0")
    return parse_exams(page, semester)
