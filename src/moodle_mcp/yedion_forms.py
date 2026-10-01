# shared helpers for Yedion pages: form fields, the student query forms, result grids
import html
import re
from datetime import date

from moodle_mcp import runi

# Yedion's query pages (timetable, exam notebooks, ...) share one form: year R1C1, semester R1C2,
# and hidden TZ (student id), Token and QueryCode (the page's menu number); "ביצוע" submits it
QUERY_SUBMIT = ("StudentQueryExecution", "TZ,Token,QueryCode,R1C1,R1C2")
NO_DATA = "אין נתונים בטווח שנבחר"  # shown instead of the results when the query finds nothing


def current_academic_year(today: date | None = None) -> int:
    """Academic years run October to September and are named by the year they end in:
    2026-10-01 .. 2027-09-30 is 2027 (תשפ"ז)."""
    today = today or date.today()
    return today.year + 1 if today.month >= 10 else today.year


def text(fragment: str) -> str:
    """HTML cell -> plain text ("&nbsp;", <br> and other tags become spaces)."""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def options(page: str, select: str) -> list[str]:
    """Numeric option values of a <select> (skips the disabled "choose..." placeholder)."""
    block = re.search(rf'(?s)<select[^>]*name="{select}".*?</select>', page)
    return re.findall(r'<option[^>]*value="?(\d+)"?', block.group()) if block else []


def hidden(page: str, name: str) -> str:
    # TZ and Token identify the student: keep their values out of error messages
    match = re.search(rf'<input[^>]*name="{name}"[^>]*value="([^"]*)"', page)
    if not match:
        raise runi.RuniError(f"Yedion's form is missing the {name} field; the page layout may have changed.")
    return match.group(1)


def grids(page: str, raw: bool = False) -> list[tuple[list[str], list[dict[str, str]]]]:
    """Every result grid on the page (div.row / div.col inside a "Table container" card):
    [(header, [{header: cell text}, ...]), ...]. Rows with a different cell count are skipped.
    raw=True keeps each cell's HTML instead of its text (e.g. to see whether it has a button)."""
    found = []
    for start in [m.start() for m in re.finditer(r'class="(?:PrintAsBox )?Table container', page)]:
        end = min([i for i in (page.find('class="card', start), page.find("</article>", start)) if i >= 0] or [len(page)])
        rows = [re.findall(r'(?s)<div class="col[^"]*">(.*?)</div>', row)
                for row in re.split(r'<div class="row[^"]*">', page[start:end])[1:]]
        if rows:
            header = [text(cell) for cell in rows[0]]
            rows = rows if raw else [[text(cell) for cell in r] for r in rows]
            found.append((header, [dict(zip(header, r)) for r in rows[1:] if len(r) == len(header)]))
    return found


def run_query(menu_number: int, year: int, semester: int) -> str:
    """Open a query page from the menu (MenuCall -N<menu_number>), check year and semester
    against its options and submit it. Returns the results page HTML. Two requests."""
    form = runi.fetch("MenuCall", f"-N,-N,-N{menu_number},-A")
    years = options(form, "R1C1")
    if str(year) not in years:
        raise ValueError(f"Yedion has no data for {year}. Available years: {', '.join(years[:12])}, ...")
    semesters = options(form, "R1C2")
    if str(semester) not in semesters:
        raise ValueError(f"Invalid semester {semester}: use one of {', '.join(semesters)} (0 = the whole year).")
    return runi.fetch(*QUERY_SUBMIT, TZ=hidden(form, "TZ"), Token=hidden(form, "Token"),
                      QueryCode=hidden(form, "QueryCode"), R1C1=str(year), R1C2=str(semester))
