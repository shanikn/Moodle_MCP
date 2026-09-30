import json
import time
from datetime import date, datetime

import pytest

from moodle_mcp import assignments
from moodle_mcp.assignments import get_assignment, list_assignments, new_assignments

NOW = int(time.time())
DAY = 86400
MIDNIGHT = int(datetime.combine(date.today(), datetime.min.time()).timestamp())


def assign(id, name, due, modified=NOW - 30 * DAY, team=0, **extra):
    return {"id": id, "cmid": id + 1000, "name": name, "duedate": due, "cutoffdate": 0,
            "timemodified": modified, "teamsubmission": team, "intro": "", **extra}


def course(fullname, *items):
    return {"id": 1, "fullname": fullname, "assignments": list(items)}


def status_answer(status, team=False):
    key = "teamsubmission" if team else "submission"
    return {"lastattempt": {key: {"status": status}}}


@pytest.fixture
def three_assignments(moodle):
    moodle.on("mod_assign_get_assignments", {"courses": [
        course("Networks",
               assign(1, "HW late", NOW - 2 * DAY),
               assign(2, "HW next week", NOW + 7 * DAY),
               assign(3, "HW tomorrow", NOW + DAY, team=1)),
        course("Probability", assign(4, "Reading", 0)),  # no due date
    ]})
    return moodle


def test_list_hides_overdue_and_sorts_by_due(three_assignments):
    result = list_assignments()
    assert [a["name"] for a in result] == ["HW tomorrow", "HW next week", "Reading"]
    first = result[0]
    assert first["course"] == "Networks"
    assert first["url"] == "https://moodle.test/2026/mod/assign/view.php?id=1003"
    assert "_team" not in first and "status" not in first


def test_list_include_overdue(three_assignments):
    assert [a["id"] for a in list_assignments(include_overdue=True)] == [1, 3, 2, 4]


def test_status_filters_use_team_submission_when_needed(three_assignments):
    answers = {"1": status_answer("new"), "2": status_answer("submitted"),
               "3": status_answer("draft", team=True), "4": status_answer("new")}
    three_assignments.on("mod_assign_get_submission_status", lambda p: answers[p["assignid"]])

    pending = list_assignments("pending", include_overdue=True)
    assert {a["id"]: a["status"] for a in pending} == {1: "new", 3: "draft", 4: "new"}
    assert [a["id"] for a in list_assignments("submitted")] == [2]


def test_all_status_makes_no_per_assignment_calls(three_assignments):
    list_assignments()
    assert three_assignments.calls_to("mod_assign_get_submission_status") == []


def test_invalid_status():
    with pytest.raises(ValueError, match="status must be one of"):
        list_assignments("done")


def test_get_assignment_details(moodle):
    moodle.on("mod_assign_get_assignments", {"courses": [course("Networks", assign(
        7, "HW 1", NOW + DAY, intro="<p>Solve&nbsp;Q1</p>",
        introattachments=[{"filename": "hw1.pdf", "fileurl": "https://moodle.test/2026/webservice/pluginfile.php/hw1.pdf"}],
    ))]})
    moodle.on("mod_assign_get_submission_status", {
        "lastattempt": {"gradingstatus": "graded", "submission": {"status": "submitted", "timemodified": NOW, "plugins": [
            {"type": "file", "fileareas": [{"files": [{"filename": "me.pdf", "fileurl": "https://moodle.test/2026/webservice/pluginfile.php/me.pdf"}]}]},
        ]}},
        "feedback": {"gradefordisplay": "48.00&nbsp;/&nbsp;100.00", "plugins": [
            {"type": "comments", "editorfields": [{"text": "<p>Check Q2</p>"}]},
            {"type": "editpdf", "fileareas": [{"files": [
                {"filename": "combined.pdf", "fileurl": "https://moodle.test/2026/webservice/pluginfile.php/c.pdf"},
                {"filename": "image_page0.png", "fileurl": "https://moodle.test/2026/webservice/pluginfile.php/i.png"},
            ]}]},
        ]},
    })

    a = get_assignment(7)
    assert a["description"] == "Solve\xa0Q1"
    assert a["attachments"] == [{"filename": "hw1.pdf", "url": "https://moodle.test/2026/pluginfile.php/hw1.pdf"}]
    assert a["submission"]["status"] == "submitted"
    assert a["submission"]["files"][0]["filename"] == "me.pdf"
    assert a["submission"]["grading_status"] == "graded"
    assert a["grade"] == "48.00\xa0/\xa0100.00"
    assert a["feedback_comments"] == "Check Q2"
    assert [f["filename"] for f in a["feedback_files"]] == ["combined.pdf"]
    assert "wstoken" not in json.dumps(a) and "token-2026" not in json.dumps(a)


def test_get_assignment_unknown_id(moodle):
    moodle.on("mod_assign_get_assignments", {"courses": [course("Networks")]})
    with pytest.raises(ValueError, match="No assignment with id 99"):
        get_assignment(99)


def test_new_assignments_baseline_then_detects_new_and_updated(moodle):
    old = assign(1, "Old", NOW + DAY)
    edited = assign(2, "Edited today", NOW + DAY, modified=MIDNIGHT + 1)
    listing = {"courses": [course("Networks", old, edited)]}
    moodle.on("mod_assign_get_assignments", listing)

    first = new_assignments()
    assert first["first_run"] is True
    assert first["new"] == []  # the first run only records a baseline
    assert [a["id"] for a in first["updated"]] == [2]

    listing["courses"][0]["assignments"].append(assign(3, "Brand new", NOW + 5 * DAY))
    second = new_assignments()
    assert second["first_run"] is False
    assert [a["id"] for a in second["new"]] == [3]
    assert [a["id"] for a in second["updated"]] == [2]

    # still "new" when asked again the same day
    assert [a["id"] for a in new_assignments()["new"]] == [3]

    # the next day it is no longer new
    state_file = assignments.STATE_DIR / "seen_assignments_2026.json"
    seen = json.loads(state_file.read_text())
    seen["3"]["first_seen"] = MIDNIGHT - DAY
    state_file.write_text(json.dumps(seen))
    assert new_assignments()["new"] == []
