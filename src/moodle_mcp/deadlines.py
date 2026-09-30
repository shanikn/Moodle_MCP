# the logic for upcoming deadlines (Moodle's calendar "timeline")
import time

from moodle_mcp.client import call
from moodle_mcp.formatting import fmt_date, html_to_text

DAY = 86400


def upcoming_deadlines(days: int = 14, include_overdue: bool = False, year: int | None = None) -> list[dict]:
    now = int(time.time())
    events = call(
        "core_calendar_get_action_events_by_timesort", year=year,
        # overdue items stay on the timeline until submitted; look back 30 days for them
        timesortfrom=now - 30 * DAY if include_overdue else now,
        timesortto=now + days * DAY, limitnum=50,
    )["events"]
    return [{
        "name": e.get("activityname") or e["name"],
        "type": e.get("modulename"),  # assign, quiz, ...
        "course": html_to_text(e["course"]["fullname"]),
        "due": fmt_date(e["timesort"]),
        "overdue": bool(e.get("overdue")),
        "action": (e.get("action") or {}).get("name"),  # e.g. "Add submission", "Attempt quiz"
        "url": e.get("url"),
    } for e in events]
