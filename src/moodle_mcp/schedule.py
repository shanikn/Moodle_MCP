# the student's class timetable (רשימת מערכת שעות) from Yedion
import re

from moodle_mcp import runi
from moodle_mcp.yedion_forms import NO_DATA, current_academic_year, grids, run_query

# menu item "רשימת מערכת שעות" (list view); the calendar view "לוח מערכת שעות" (-N16) has no grid
TIMETABLE_MENU = 3
DAYS = {"ראשון": "Sunday", "שני": "Monday", "שלישי": "Tuesday", "רביעי": "Wednesday",
        "חמישי": "Thursday", "שישי": "Friday", "שבת": "Saturday"}
WEEK_ORDER = list(DAYS.values())
MEETING = re.compile(r"יום\s+(\S+)\s+(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})")  # "יום שני 11:15 - 08:45"
NOTE_REF = re.compile(r"\s*\(הערה:\s*([\d,\s]+)\)")                        # "רשתות (הערה:1)"
GROUP = re.compile(r"\s*\(קבוצה:\s*(\d+)\)")                                # "תרגול (קבוצה:4)"


def _number(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def _meetings(cell: str) -> list[dict]:
    """"יום שני 11:15 - 08:45" -> [{"day": "Monday", "start": "08:45", "end": "11:15"}]; "-" -> []."""
    meetings = []
    for day, a, b in MEETING.findall(cell):
        start, end = sorted((a.zfill(5), b.zfill(5)))  # Yedion writes the later time first
        meetings.append({"day": DAYS.get(day, day), "start": start, "end": end})
    return meetings


def _sort_key(course: dict):
    first = course["meetings"][0] if course["meetings"] else None
    day = WEEK_ORDER.index(first["day"]) if first and first["day"] in WEEK_ORDER else 7
    return (str(course["semester"]), day, first["start"] if first else "")


def parse_schedule(page: str, semester: int | None = None) -> dict:
    """Courses from the results grid, with the notes (הערות) table resolved and the totals from
    the summary (סיכום) table. `semester` fills in the semester if the column is missing."""
    found = grids(page)
    main = next(((h, rows) for h, rows in found if "קוד קורס" in h and "יום ושעות" in h), None)
    if main is None:
        if NO_DATA in page:
            return {"courses": [], "total_credits": 0.0, "total_weekly_hours": 0.0}
        raise runi.RuniError("Yedion's timetable page has no results table; the page layout may have changed.")
    notes = {}
    for header, rows in found:
        if len(header) == 2 and "קוד הערה" in header[0]:
            notes = {row[header[0]]: row[header[1]] for row in rows}
    totals = next((rows for h, rows in found if "סך הכל נקודות זכות" in h), [])

    courses = []
    for row in main[1]:
        name = row["שם הקורס"]
        refs = [code.strip() for match in NOTE_REF.findall(name) for code in match.split(",") if code.strip()]
        kind = row.get("סוג מקצוע", "")
        group = GROUP.search(kind)
        courses.append({
            "course": NOTE_REF.sub("", name).strip(),
            "course_number": row["קוד קורס"],
            "semester": int(row["סמסטר"]) if row.get("סמסטר", "").isdigit() else semester,
            "type": GROUP.sub("", kind).strip().lstrip("- ").strip() or None,
            "group": int(group.group(1)) if group else None,
            "lecturer": row.get("שם המרצה") or None,
            "credits": _number(row.get("נקודות זכות", "")),
            "weekly_hours": _number(row.get('ש"ס', "")),
            "meetings": _meetings(row.get("יום ושעות", "")),
            "room": row.get("חדר") or None,
            "notes": [notes.get(code, f"note {code}") for code in refs],
        })
    return {
        "courses": sorted(courses, key=_sort_key),
        "total_credits": sum(_number(r.get("סך הכל נקודות זכות", "")) or 0 for r in totals),
        "total_weekly_hours": sum(_number(r.get('סך הכל ש"ס', "")) or 0 for r in totals),
    }


def class_schedule(year: int | None = None, semester: int | None = None) -> dict:
    year = current_academic_year() if year is None else year
    page = run_query(TIMETABLE_MENU, year, semester or 0)
    return parse_schedule(page, semester)
