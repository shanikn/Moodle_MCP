# plain-text summaries for iPhone Shortcuts: "What's due?" (/<secret>/due) and upcoming exams (/<secret>/exams)
from datetime import datetime

import httpx

from moodle_mcp import deadlines, exams, schedule
from moodle_mcp.runi import RuniError
from moodle_mcp.yedion_forms import current_academic_year

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


def countdown(days: int) -> str:
    return "today" if days == 0 else "tomorrow" if days == 1 else f"in {days} days"


def upcoming_exams(days: int | None = None, now: datetime | None = None) -> dict:
    """{"text", "exams"}: exams from today on (within `days` days if given), soonest first, from
    Yedion's exam schedule. Looks at the current academic year and the one before it: a late moed
    of last year's course (e.g. in October) is still listed under last year. Older years cannot
    hold a future exam. Courses with an alternative assessment (no exam to sit) and exams without
    a date yet are left out."""
    now = now or datetime.now()
    this_year = current_academic_year(now.date())
    listed = exams.exam_schedule(this_year)
    try:
        listed = exams.exam_schedule(this_year - 1) + listed
    except ValueError:  # Yedion has no schedule for last year (e.g. a first-year student)
        pass
    found = []
    for exam in listed:
        if not exam["date"] or exam["alternative_assessment"]:
            continue
        left = (datetime.strptime(exam["date"], "%Y-%m-%d").date() - now.date()).days
        if left >= 0 and (days is None or left <= days):
            found.append({**exam, "days_left": left})

    found.sort(key=lambda e: (e["date"], e["start"] or ""))
    if not found:
        return {"text": "No upcoming exams" + (f" in the next {days} days." if days else "."), "exams": []}
    lines = ["Upcoming exams:"]
    for exam in found:
        day = datetime.strptime(exam["date"], "%Y-%m-%d")
        moed = "special moed" if exam["moed"] == "special" else f"moed {exam['moed']}"
        details = [moed] + ([f"room {exam['room']}"] if exam["room"] else [])
        if exam["registered"] is False:
            details.append("NOT REGISTERED")
        lines.append(f"• {day.strftime('%a')} {day.day}/{day.month}" + (f" {exam['start']}" if exam["start"] else "")
                     + f" ({countdown(exam['days_left'])}): {exam['course']}, {', '.join(details)}")
    return {"text": "\n".join(lines), "exams": found}
