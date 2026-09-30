#  the logic for listing all assignments and for the snapshot comparison (options A and B)
import html
import json
import re
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


def _text(raw: str) -> str:
    """Moodle HTML -> plain text (keeps line breaks)."""
    raw = re.sub(r"<br\s*/?>|</p>|</div>|</li>", "\n", raw or "", flags=re.I)
    raw = html.unescape(re.sub(r"<[^>]+>", "", raw))
    return re.sub(r"\n\s*\n+", "\n\n", raw).strip()


def _browser_url(fileurl: str) -> str:
    """Web-service file links need the token; the plain pluginfile link works in a logged-in browser."""
    return fileurl.replace("/webservice/pluginfile.php", "/pluginfile.php")


def _files(fileareas: list[dict]) -> list[dict]:
    return [
        {"filename": f["filename"], "url": _browser_url(f["fileurl"])}
        for area in fileareas
        for f in area.get("files", [])
        # editpdf stores one preview image per page next to the annotated combined.pdf
        if not f["filename"].startswith("image_page")
    ]


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


def get_assignment(assignment_id: int, year: int | None = None) -> dict:
    """Full details of one assignment: task text, attachments, your submission, grade and feedback."""
    site = get_site(year)
    for course in call("mod_assign_get_assignments", year=year)["courses"]:
        a = next((x for x in course["assignments"] if x["id"] == assignment_id), None)
        if a:
            break
    else:
        raise ValueError(f"No assignment with id {assignment_id} in {site.url}")

    status = call("mod_assign_get_submission_status", year=year, assignid=assignment_id)
    attempt = status.get("lastattempt") or {}
    submission = (attempt.get("teamsubmission") if a["teamsubmission"] else attempt.get("submission")) or {}
    feedback = status.get("feedback") or {}
    feedback_plugins = feedback.get("plugins", [])

    return {
        "id": a["id"],
        "name": a["name"],
        "course": course["fullname"],
        "due": _date(a["duedate"]),
        "cutoff": _date(a["cutoffdate"]),
        "url": f"{site.url}/mod/assign/view.php?id={a['cmid']}",
        "description": _text(a["intro"]),
        "attachments": _files([{"files": a.get("introattachments", [])}]),
        "submission": {
            "status": submission.get("status", "new"),
            "last_modified": _date(submission.get("timemodified", 0)),
            "files": _files([fa for p in submission.get("plugins", []) for fa in p.get("fileareas", [])]),
            "grading_status": attempt.get("gradingstatus"),
        },
        "grade": _text(feedback["gradefordisplay"]) if feedback.get("gradefordisplay") else None,
        "feedback_comments": "\n\n".join(
            t for p in feedback_plugins for e in p.get("editorfields", []) if (t := _text(e.get("text", "")))
        ) or None,
        "feedback_files": _files([fa for p in feedback_plugins for fa in p.get("fileareas", [])]),
    }


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
