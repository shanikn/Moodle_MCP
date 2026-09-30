import time

import pytest

from moodle_mcp.calendar import calendar_events

NOW = int(time.time())
COURSES = [{"id": 11, "fullname": "Computer Networks"}, {"id": 12, "fullname": "Algorithms"}]


def event(**fields):
    return {"name": "x", "description": "", "courseid": 0, "eventtype": "site", "modulename": "",
            "timestart": NOW + 3600, "timeduration": 0, **fields}


@pytest.fixture
def cal(moodle):
    moodle.on("core_enrol_get_users_courses", COURSES)
    return moodle


def test_shapes_events_sorted_by_start(cal):
    cal.on("core_calendar_get_calendar_events", {"events": [
        event(name="HW 1 due", courseid=11, eventtype="due", modulename="assign", timestart=NOW + 7200),
        event(name="מבחן מועד ב", courseid=12, eventtype="course", timestart=NOW + 3600, timeduration=10800,
              location="Room 101", description="<p>Bring <b>ID</b></p>"),
        event(name="Semester break", eventtype="site", timestart=NOW + 9000),
    ], "warnings": []})
    exam, hw, site = calendar_events(days=7)
    assert exam["name"] == "מבחן מועד ב" and exam["course"] == "Algorithms" and exam["type"] == "course"
    assert exam["location"] == "Room 101" and exam["description"] == "Bring ID"
    assert exam["end"] is not None and exam["end"] > exam["start"]
    assert "activity" not in exam
    assert exam["url"] == f"https://moodle.test/2026/calendar/view.php?view=day&time={NOW + 3600}"
    assert hw["activity"] == "assign" and hw["type"] == "due" and hw["end"] is None
    assert "location" not in hw and "description" not in hw
    assert site["course"] is None and site["type"] == "site"


def test_requests_window_and_all_courses(cal):
    cal.on("core_calendar_get_calendar_events", {"events": []})
    calendar_events(days=30)
    sent = cal.calls_to("core_calendar_get_calendar_events")[0]
    assert int(sent["options[timeend]"]) - int(sent["options[timestart]"]) == 30 * 86400
    assert int(sent["options[timestart]"]) >= NOW
    assert sent["options[siteevents]"] == "1" and sent["options[userevents]"] == "1"
    assert [sent["events[courseids][0]"], sent["events[courseids][1]"]] == ["11", "12"]


def test_course_filter_drops_other_events(cal):
    cal.on("core_calendar_get_calendar_events", {"events": [
        event(name="Exam", courseid=11, eventtype="course"), event(name="Holiday", eventtype="site"),
    ]})
    assert [e["name"] for e in calendar_events(course_id=11)] == ["Exam"]
    sent = cal.calls_to("core_calendar_get_calendar_events")[0]
    assert sent["events[courseids][0]"] == "11" and "events[courseids][1]" not in sent


def test_long_description_is_trimmed(cal):
    cal.on("core_calendar_get_calendar_events", {"events": [event(description="a" * 900)]})
    [item] = calendar_events()
    assert len(item["description"]) == 501 and item["description"].endswith("…")


def test_bad_input(cal):
    with pytest.raises(ValueError, match="not one of your courses"):
        calendar_events(course_id=99)
    with pytest.raises(ValueError, match="at least 1"):
        calendar_events(days=0)
