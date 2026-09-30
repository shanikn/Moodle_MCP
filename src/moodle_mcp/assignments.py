#  the logic for listing all assignments and for the snapshot comparison (options A and B)
import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from pathlib import Path

from moodle_mcp.client import call
from moodle_mcp.config import MOODLE_DEFAULT_YEAR, get_site

STATUSES = ("all", "pending", "submitted")
# project root/.state (git-ignored): remembers which assignments were already seen
STATE_DIR = Path(__file__).resolve().parents[2] / ".state"


def _date(ts: int) -> str | None:
    """Moodle uses Unix timestamps; 0 means 'not set'."""
    if ts == 0:
        return None
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def _submission_status(assign_id: int, team: bool, year: int | None) -> str:
    """'submitted', 'draft' or 'new' (nothing handed in)."""
    result = call("mod_assign_get_submission_status", year=year, assignid=assign_id)
    attempt = result.get("lastattempt") or {}
    submission = attempt.get("teamsubmission") if team else attempt.get("submission")
    return (submission or {}).get("status", "new")


def list_assignments(status: str = "all", include_overdue: bool = False, year: int | None = None) -> list[dict]:
    if status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}, got {status!r}")
    site = get_site(year)
    result = call("mod_assign_get_assignments", year=year)
    now = time.time()
    assignments = []
    for course in result["courses"]:
        for a in course["assignments"]:
            if not include_overdue and a["duedate"] and a["duedate"] < now:
                continue
            assignments.append({
                "id": a["id"],
                "name": a["name"],
                "course": course["fullname"],
                "due": _date(a["duedate"]),
                "cutoff": _date(a["cutoffdate"]),
                "url": f"{site.url}/mod/assign/view.php?id={a['cmid']}",
                "timemodified": a["timemodified"],
                "_team": bool(a["teamsubmission"]),
            })

    if status != "all":
        # one API call per assignment, so run them in parallel
        with ThreadPoolExecutor(max_workers=8) as pool:
            statuses = pool.map(lambda a: _submission_status(a["id"], a["_team"], year), assignments)
            for a, s in zip(assignments, list(statuses)):
                a["status"] = s
        wanted = {"submitted"} if status == "submitted" else {"new", "draft"}
        assignments = [a for a in assignments if a["status"] in wanted]

    for a in assignments:
        del a["_team"]
    assignments.sort(key=lambda x: x["due"] or "9999")
    return assignments


def new_assignments(year: int | None = None) -> dict:
    """Assignments added today (not seen before) and ones updated today.

    Moodle has no 'created' date, so each assignment's first-seen time is kept in
    .state/seen_assignments_<year>.json. The first run only records a baseline;
    until then, anything with timemodified today is reported as updated.
    """
    year = year or MOODLE_DEFAULT_YEAR
    state_file = STATE_DIR / f"seen_assignments_{year}.json"
    first_run = not state_file.exists()
    seen = {} if first_run else json.loads(state_file.read_text(encoding="utf-8"))

    now = time.time()
    midnight = datetime.combine(date.today(), datetime.min.time()).timestamp()
    new, updated = [], []
    for a in list_assignments(include_overdue=True, year=year):
        key = str(a["id"])
        if key not in seen:
            # first run: baseline, so first_seen = 0 (not "new today")
            seen[key] = {"first_seen": 0 if first_run else now}
        if seen[key]["first_seen"] >= midnight:
            new.append(a)
        elif a["timemodified"] >= midnight:
            updated.append(a)

    STATE_DIR.mkdir(exist_ok=True)
    state_file.write_text(json.dumps(seen, indent=1), encoding="utf-8")
    return {"first_run": first_run, "new": new, "updated": updated}
