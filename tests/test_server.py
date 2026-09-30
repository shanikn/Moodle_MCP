import asyncio
import json

import httpx
import pytest
from mcp.server.mcpserver.exceptions import ToolError

from moodle_mcp.server import mcp

TOOLS = {"list_assignments", "get_assignment", "new_assignments", "list_courses",
         "get_course_staff", "get_course_contents", "get_grades", "staff_messages",
         "upcoming_deadlines", "calendar_events", "search_moodle", "read_content"}


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


def test_staff_messages_returns_one_json_object(moodle):
    moodle.on("core_enrol_get_users_courses", [])
    moodle.on("mod_forum_get_forums_by_courses", [])
    moodle.on("core_message_get_conversations", {"conversations": []})
    result = call_tool("staff_messages", {})
    assert len(result.content) == 1
    assert json.loads(result.content[0].text) == {"messages": []}
