import asyncio

from moodle_mcp.server import mcp

TOOLS = {"list_assignments", "get_assignment", "new_assignments", "list_courses",
         "get_course_staff", "get_course_contents", "get_grades", "staff_messages",
         "upcoming_deadlines", "search_moodle", "read_content"}


def test_all_tools_registered_and_read_only():
    tools = asyncio.run(mcp.list_tools())
    assert {t.name for t in tools} == TOOLS
    for t in tools:
        assert t.annotations.read_only_hint, t.name
        assert len(t.description) > 50, f"{t.name} needs a real description for Claude"


def test_status_is_limited_to_valid_values():
    tool = next(t for t in asyncio.run(mcp.list_tools()) if t.name == "list_assignments")
    assert tool.input_schema["properties"]["status"]["enum"] == ["all", "pending", "submitted"]
