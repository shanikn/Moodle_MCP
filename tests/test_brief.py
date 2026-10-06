from datetime import datetime

from starlette.testclient import TestClient

from moodle_mcp import brief, exams, schedule
from moodle_mcp.runi import RuniError
from moodle_mcp.server import http_app

NOW = datetime(2026, 10, 6, 21, 0)  # a Tuesday, semester 1
SECRET = "s" * 40


def event(name, due: datetime, overdue=False):
    return {"name": name, "activityname": name, "modulename": "assign", "course": {"fullname": "Networks"},
            "timesort": int(due.timestamp()), "overdue": overdue, "action": {"name": "Add submission"}, "url": "u"}


def timetable(*courses):
    return lambda *args, **kwargs: {"courses": list(courses), "total_credits": 0.0, "total_weekly_hours": 0.0}


def course(name, day, start, end, semester=1, kind="שיעור", room="C110"):
    return {"course": name, "semester": semester, "type": kind, "room": room,
            "meetings": [{"day": day, "start": start, "end": end}]}


def test_when_is_relative_to_today():
    assert brief.when("2026-10-06 23:59", NOW) == "Today 23:59"
    assert brief.when("2026-10-07 08:00", NOW) == "Tomorrow 08:00"
    assert brief.when("2026-10-11 12:00", NOW) == "Sunday 12:00"
    assert brief.when("2026-10-20 12:00", NOW) == "Tue 20/10"  + " 12:00"


def test_current_semester():
    assert [brief.current_semester(datetime(2026, m, 1)) for m in (10, 1, 2, 3, 6, 7, 9)] == [1, 1, 1, 2, 2, 3, 3]


def test_text_lists_todays_classes_then_deadlines_soonest_first(moodle, monkeypatch):
    monkeypatch.setattr(schedule, "class_schedule", timetable(
        course("Algorithms", "Tuesday", "12:00", "14:00"),
        course("Networks", "Tuesday", "08:45", "11:15", room=None),
        course("Databases", "Monday", "09:00", "11:00"),            # another day
        course("Summer course", "Tuesday", "09:00", "11:00", semester=2),  # another semester
    ))
    moodle.on("core_calendar_get_action_events_by_timesort", {"events": [
        event("HW 2", datetime(2026, 10, 9, 23, 59)), event("HW 1", datetime(2026, 10, 7, 23, 59))]})
    result = brief.whats_due(now=NOW)
    assert result["text"] == ("Today, Tuesday:\n"
                              "• 08:45-11:15 Networks (שיעור)\n"
                              "• 12:00-14:00 Algorithms (שיעור, C110)\n"
                              "\n"
                              "Due in the next 7 days:\n"
                              "• Tomorrow 23:59: HW 1 (Networks)\n"
                              "• Friday 23:59: HW 2 (Networks)")
    assert [d["name"] for d in result["deadlines"]] == ["HW 1", "HW 2"]
    assert [c["course"] for c in result["classes"]] == ["Networks", "Algorithms"]


def test_nothing_due_and_no_classes(moodle, monkeypatch):
    monkeypatch.setattr(schedule, "class_schedule", timetable())
    moodle.on("core_calendar_get_action_events_by_timesort", {"events": []})
    assert brief.whats_due(days=3, now=NOW)["text"] == "No classes today.\n\nNothing due in the next 3 days."


def test_yedion_failure_still_returns_deadlines(moodle, monkeypatch):
    def broken(*args, **kwargs):
        raise RuniError("Yedion is down")
    monkeypatch.setattr(schedule, "class_schedule", broken)
    moodle.on("core_calendar_get_action_events_by_timesort", {"events": [event("HW 1", datetime(2026, 10, 7, 10, 0))]})
    result = brief.whats_due(now=NOW)
    assert result["classes"] is None
    assert result["text"].startswith("Couldn't load today's classes.\n\nDue in the next 7 days:\n• Tomorrow 10:00: HW 1")


def test_classes_can_be_skipped_and_overdue_is_marked(moodle, monkeypatch):
    monkeypatch.setattr(schedule, "class_schedule", lambda *a, **k: 1 / 0)  # must not be called
    moodle.on("core_calendar_get_action_events_by_timesort",
              {"events": [event("Old HW", datetime(2026, 10, 5, 23, 59), overdue=True)]})
    result = brief.whats_due(classes=False, include_overdue=True, now=NOW)
    assert result["text"] == "Due in the next 7 days:\n• OVERDUE, was Mon 5/10 23:59: Old HW (Networks)"


# --- the HTTP endpoint ---


def test_due_endpoint_returns_plain_text_and_json(moodle, monkeypatch):
    monkeypatch.setattr(schedule, "class_schedule", timetable())
    moodle.on("core_calendar_get_action_events_by_timesort", {"events": []})
    client = TestClient(http_app(SECRET))
    answer = client.get(f"/{SECRET}/due?days=3")
    assert answer.status_code == 200 and answer.headers["content-type"].startswith("text/plain")
    assert answer.text == "No classes today.\n\nNothing due in the next 3 days."
    data = client.get(f"/{SECRET}/due?format=json&classes=0").json()
    assert data == {"text": "Nothing due in the next 7 days.", "deadlines": [], "classes": None}


def test_due_endpoint_rejects_bad_days_and_reports_moodle_errors(moodle):
    client = TestClient(http_app(SECRET))
    assert client.get(f"/{SECRET}/due?days=abc").status_code == 400
    assert client.get(f"/{SECRET}/due?days=0").status_code == 400
    moodle.on("core_calendar_get_action_events_by_timesort",
              {"exception": "x", "errorcode": "invalidtoken", "message": "Invalid token"})
    answer = client.get(f"/{SECRET}/due?classes=0")
    assert answer.status_code == 502 and "invalidtoken" in answer.text


def test_due_endpoint_is_only_reachable_with_the_secret(moodle):
    client = TestClient(http_app(SECRET))
    assert client.get("/due").status_code == 404
    assert client.get("/wrong-secret/due").status_code == 404


# --- upcoming exams ---


def exam(course, date, start="09:00", moed=1, room=None, registered=True, alternative=None):
    return {"course": course, "course_number": "1", "lecturer": None, "semester": 1, "moed": moed, "type": "מבחן סופי",
            "date": date, "start": start, "room": room, "registered": registered, "appeal_deadline": None,
            "alternative_assessment": alternative}


def test_upcoming_exams_text(monkeypatch):
    monkeypatch.setattr(exams, "exam_schedule", lambda *a, **k: [
        exam("Old exam", "2026-10-05"),                               # already passed
        exam("Networks", "2026-10-06", room="C110"),                  # today counts
        exam("Algorithms", "2026-10-07", moed=2, registered=False),
        exam("Project course", "2026-10-08", alternative="פרויקט"),    # nothing to sit
        exam("No date yet", None),
        exam("Databases", "2027-01-31", start=None, moed="special"),
    ])
    result = brief.upcoming_exams(now=NOW)
    assert result["text"] == ("Upcoming exams:\n"
                              "• Tue 6/10 09:00 (today): Networks, moed 1, room C110\n"
                              "• Wed 7/10 09:00 (tomorrow): Algorithms, moed 2, NOT REGISTERED\n"
                              "• Sun 31/1 (in 117 days): Databases, special moed")
    assert [e["days_left"] for e in result["exams"]] == [0, 1, 117]
    assert [e["course"] for e in brief.upcoming_exams(days=7, now=NOW)["exams"]] == ["Networks", "Algorithms"]


def test_no_upcoming_exams(monkeypatch):
    monkeypatch.setattr(exams, "exam_schedule", lambda *a, **k: [exam("Old exam", "2026-10-05")])
    assert brief.upcoming_exams(now=NOW)["text"] == "No upcoming exams."
    assert brief.upcoming_exams(days=30, now=NOW)["text"] == "No upcoming exams in the next 30 days."


def test_exams_endpoint(monkeypatch):
    monkeypatch.setattr(exams, "exam_schedule", lambda *a, **k: [])
    client = TestClient(http_app(SECRET))
    answer = client.get(f"/{SECRET}/exams")
    assert answer.status_code == 200 and answer.text == "No upcoming exams."
    assert client.get(f"/{SECRET}/exams?format=json").json() == {"text": "No upcoming exams.", "exams": []}
    assert client.get(f"/{SECRET}/exams?days=x").status_code == 400
    assert client.get("/exams").status_code == 404


def test_exams_endpoint_reports_yedion_errors(monkeypatch):
    def broken(*args, **kwargs):
        raise RuniError("My RUNI refused the username or password")
    monkeypatch.setattr(exams, "exam_schedule", broken)
    answer = TestClient(http_app(SECRET)).get(f"/{SECRET}/exams")
    assert answer.status_code == 502 and "refused" in answer.text


def test_upcoming_exams_include_last_academic_year(monkeypatch):
    # 2026-10-06 is academic year 2027; a late moed of a 2026 course is listed under 2026
    by_year = {2027: [exam("Algorithms", "2027-01-31")], 2026: [exam("Networks", "2026-10-20", moed=3)]}
    asked = []

    def schedule_for(year=None, semester=None):
        asked.append(year)
        return by_year[year]
    monkeypatch.setattr(exams, "exam_schedule", schedule_for)
    assert [e["course"] for e in brief.upcoming_exams(now=NOW)["exams"]] == ["Networks", "Algorithms"]
    assert asked == [2027, 2026]


def test_upcoming_exams_without_last_year(monkeypatch):
    def schedule_for(year=None, semester=None):
        if year == 2026:
            raise ValueError("Yedion has no exam schedule for 2026.")
        return [exam("Algorithms", "2027-01-31")]
    monkeypatch.setattr(exams, "exam_schedule", schedule_for)
    assert [e["course"] for e in brief.upcoming_exams(now=NOW)["exams"]] == ["Algorithms"]
