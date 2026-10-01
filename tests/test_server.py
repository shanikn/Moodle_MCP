import asyncio
import json
import os
import subprocess
import sys

import httpx
import pytest
from mcp.server.mcpserver.exceptions import ToolError

from moodle_mcp.server import mcp
from tests.conftest import FIXTURES

EXAM_FORM = (FIXTURES / "yedion_exam_form.html").read_text(encoding="utf-8")
NO_EXAMS = (FIXTURES / "yedion_no_exams.html").read_text(encoding="utf-8")

TOOLS = {"list_assignments", "get_assignment", "new_assignments", "list_courses",
         "get_course_staff", "get_course_contents", "get_grades", "staff_messages",
         "upcoming_deadlines", "calendar_events", "search_moodle", "read_content", "exam_schedule", "class_schedule"}


def call_tool(name, args):
    return asyncio.run(mcp.call_tool(name, args))


def test_all_tools_registered_and_read_only():
    tools = asyncio.run(mcp.list_tools())
    assert {t.name for t in tools} == TOOLS
    for t in tools:
        assert t.annotations.read_only_hint, t.name
        assert len(t.description) > 50, f"{t.name} needs a real description for Claude"


def test_status_is_limited_to_valid_values():
    tool = next(t for t in asyncio.run(mcp.list_tools()) if t.name == "list_assignments")
    assert tool.input_schema["properties"]["status"]["enum"] == ["all", "pending", "submitted"]


# mcp hides the message of unexpected exceptions; these errors must reach Claude as text


def test_moodle_error_message_reaches_claude(moodle):
    moodle.on("mod_assign_get_assignments", {"exception": "x", "errorcode": "invalidtoken", "message": "Invalid token"})
    with pytest.raises(ToolError, match="invalidtoken: Invalid token"):
        call_tool("list_assignments", {})


def test_bad_input_message_reaches_claude(moodle):
    with pytest.raises(ToolError, match="Only links to your Moodle site"):
        call_tool("read_content", {"url": "https://example.com/pluginfile.php/1/x.pdf"})


def test_missing_year_message_reaches_claude(moodle):
    with pytest.raises(ToolError, match="Add MOODLE_TOKEN_2030 to .env"):
        call_tool("list_courses", {"year": 2030})


def test_network_error_message_reaches_claude(moodle):
    moodle.router.routes[0].side_effect = httpx.ConnectError("connection refused")
    with pytest.raises(ToolError, match="Could not reach Moodle: connection refused"):
        call_tool("list_courses", {})


def test_server_starts_without_yedion_credentials():
    # the hosted server deploys from main: missing RUNI_* must only break exam_schedule
    env = {k: v for k, v in os.environ.items() if not k.startswith("RUNI_")}
    code = ("import dotenv; dotenv.load_dotenv = lambda *a, **k: False; import asyncio; "
            "from moodle_mcp.server import mcp; print(len(asyncio.run(mcp.list_tools())))")
    result = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    assert int(result.stdout) == len(TOOLS)


def test_missing_yedion_credentials_only_fail_exam_schedule(runi_site, moodle, monkeypatch):
    monkeypatch.delenv("RUNI_USERNAME")
    monkeypatch.delenv("RUNI_PASSWORD")
    with pytest.raises(ToolError, match="Yedion login is not configured"):
        call_tool("exam_schedule", {})
    moodle.on("core_enrol_get_users_courses", [])
    assert json.loads(call_tool("list_courses", {}).content[0].text) == {"courses": []}
    assert runi_site.password_posts == 0


def test_yedion_error_message_reaches_claude(runi_site):
    runi_site.accepted_password = "changed"
    with pytest.raises(ToolError, match="My RUNI refused the username or password"):
        call_tool("exam_schedule", {})


# a bare list would reach the client as one content block per item instead of one JSON array


@pytest.mark.parametrize("name, args, wsfunction, answer, key", [
    ("list_assignments", {}, "mod_assign_get_assignments", {"courses": []}, "assignments"),
    ("list_courses", {}, "core_enrol_get_users_courses", [], "courses"),
    ("get_course_staff", {"course_id": 1}, "core_enrol_get_enrolled_users", [], "staff"),
    ("get_course_contents", {"course_id": 1}, "core_course_get_contents", [], "sections"),
    ("upcoming_deadlines", {}, "core_calendar_get_action_events_by_timesort", {"events": []}, "deadlines"),
    ("calendar_events", {}, "core_calendar_get_calendar_events", {"events": []}, "events"),
])
def test_list_tools_return_one_json_object(moodle, name, args, wsfunction, answer, key):
    moodle.on("core_enrol_get_users_courses", [])
    moodle.on(wsfunction, answer)
    result = call_tool(name, args)
    assert len(result.content) == 1
    assert json.loads(result.content[0].text) == {key: []}


def test_exam_schedule_returns_one_json_object(runi_site):
    runi_site.pages = {"MenuCall": EXAM_FORM, "HADPASAT_TOCHNIT_BEHINOT": NO_EXAMS}
    result = call_tool("exam_schedule", {})
    assert len(result.content) == 1
    assert json.loads(result.content[0].text) == {"exams": []}


def test_staff_messages_returns_one_json_object(moodle):
    moodle.on("core_enrol_get_users_courses", [])
    moodle.on("mod_forum_get_forums_by_courses", [])
    moodle.on("core_message_get_conversations", {"conversations": []})
    result = call_tool("staff_messages", {})
    assert len(result.content) == 1
    assert json.loads(result.content[0].text) == {"messages": []}
