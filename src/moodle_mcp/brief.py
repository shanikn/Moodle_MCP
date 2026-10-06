# "What's due?": a short plain-text summary for the iPhone Shortcut (served at /<secret>/due)
from datetime import datetime

import httpx

from moodle_mcp import deadlines, schedule
from moodle_mcp.runi import RuniError

DATE_FORMAT = "%Y-%m-%d %H:%M"  # what formatting.fmt_date() produces


def current_semester(today: datetime) -> int:
    """1 = October to February, 2 = March to June, 3 = summer (July to September)."""
    if today.month >= 10 or today.month <= 2:
        return 1
    return 2 if today.month <= 6 else 3


def when(due: str, now: datetime) -> str:
    """"2026-10-07 23:59" -> "Tomorrow 23:59" (also "Today", a weekday name within a week, else the date)."""
    moment = datetime.strptime(due, DATE_FORMAT)
    days = (moment.date() - now.date()).days
    if days == 0:
        day = "Today"
    elif days == 1:
        day = "Tomorrow"
    elif 1 < days < 7:
        day = moment.strftime("%A")
    else:
        day = f"{moment.strftime('%a')} {moment.day}/{moment.month}"
    return f"{day} {moment.strftime('%H:%M')}"


def todays_classes(now: datetime) -> list[dict]:
    """Today's sessions from the Yedion timetable, by start time. One entry per meeting."""
    weekday, semester = now.strftime("%A"), current_semester(now)
    found = []
    for course in schedule.class_schedule()["courses"]:
        if course["semester"] != semester:
            continue
        for meeting in course["meetings"]:
            if meeting["day"] == weekday:
                found.append({"course": course["course"], "type": course["type"], "room": course["room"],
                              "start": meeting["start"], "end": meeting["end"]})
    return sorted(found, key=lambda c: c["start"])


def whats_due(days: int = 7, classes: bool = True, include_overdue: bool = False,
              now: datetime | None = None) -> dict:
    """{"text", "deadlines", "classes"}: `text` is ready to show or read aloud; the lists are the
    same data for clients that want to format it themselves. classes is None when the timetable
    was skipped or Yedion could not be read (deadlines must still work then)."""
    now = now or datetime.now()
    items = sorted((d for d in deadlines.upcoming_deadlines(days, include_overdue) if d["due"]),
                   key=lambda d: d["due"])
    lines = []

    today = None
    if classes:
        try:
            today = todays_classes(now)
        except (RuniError, ValueError, httpx.HTTPError):
            lines.append("Couldn't load today's classes.")
        else:
            if today:
                lines.append(f"Today, {now.strftime('%A')}:")
                for c in today:
                    extra = ", ".join(part for part in (c["type"], c["room"]) if part)
                    lines.append(f"• {c['start']}-{c['end']} {c['course']}" + (f" ({extra})" if extra else ""))
            else:
                lines.append("No classes today.")
        lines.append("")

    if items:
        lines.append(f"Due in the next {days} days:")
        for d in items:
            prefix = "OVERDUE, was " if d["overdue"] else ""
            lines.append(f"• {prefix}{when(d['due'], now)}: {d['name']} ({d['course']})")
    else:
        lines.append(f"Nothing due in the next {days} days.")
    return {"text": "\n".join(lines), "deadlines": items, "classes": today}
