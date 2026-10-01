from functools import wraps
from typing import Literal

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

from moodle_mcp import assignments, calendar, courses, deadlines, exams, grades, messages, reading, search
from moodle_mcp.client import MoodleError
from moodle_mcp.runi import RuniError

mcp = MCPServer(
    "moodle",
    instructions=("Access to a student's Reichman University Moodle. Each academic year is a separate site; "
    "tools default to the current year unless 'year' is given. Dates are local Israel time. "
    "exam_schedule reads the university's student info station (Yedion) instead of Moodle."),
)

READ_ONLY = ToolAnnotations(read_only_hint=True)


def tool(fn):
    """Register a read-only tool. Expected failures (Moodle or Yedion errors such as an expired
    token or a refused login, bad input, network problems) become ToolError, whose message Claude sees; mcp hides the
    text of any other exception and reports only "Error executing tool"."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (MoodleError, RuniError, ValueError) as exc:
            raise ToolError(str(exc)) from exc
        except httpx.HTTPError as exc:
            raise ToolError(f"Could not reach Moodle: {exc}") from exc
    return mcp.tool(annotations=READ_ONLY)(wrapper)

@tool
def list_assignments(status: Literal["all", "pending","submitted"] = "all",
                     include_overdue: bool = False,
                     year: int | None = None) -> dict:
    """List the student's assignments across all their courses, sorted by due date.

    Returns {"assignments": [...]}. Each item has: id, name, course, due, cutoff
    (dates as "YYYY-MM-DD HH:MM" or null), url (link to the assignment in Moodle) and
    timemodified. With a status filter, each item also has status: "new" (nothing handed in), "draft" (uploaded but not
    submitted) or "submitted".

    status:
      - "all": every assignment, no submission check (fast, one request).
      - "pending": not yet submitted (new or draft). Slower: checks each assignment
        separately, so prefer it over "all" only when submission status matters.
      - "submitted": already handed in. Same cost as "pending".
      Note: "pending" can include assignments graded offline (e.g. exams) that never
      need a Moodle submission.

    include_overdue: False (default) returns only assignments whose due date has not
    passed yet, or that have no due date. Set True for past assignments too.
    """
    return {"assignments": assignments.list_assignments(status, include_overdue, year)}


@tool
def get_assignment(assignment_id: int, year: int | None = None) -> dict:
    """Full details of one assignment. Use the id from list_assignments.

    Returns the task: name, course, due, cutoff, url, description (plain text) and
    attachments (e.g. the exercise PDF); the student's submission: status
    ("new" / "draft" / "submitted"), last_modified, submitted files, grading_status;
    and the result: grade (e.g. "48.00 / 100.00", null if not graded), feedback_comments
    and feedback_files (e.g. an annotated PDF).

    File urls open in a browser where the student is logged in to Moodle; this tool
    does not download file contents.
    """
    return assignments.get_assignment(assignment_id, year)


@tool
def new_assignments(year: int | None = None) -> dict:
    """Assignments added or changed today, across all courses (including past-due ones).

    Returns {"first_run": bool, "new": [...], "updated": [...]}, with items in the same
    format as list_assignments.
      - new: assignments that appeared today (not seen on any earlier check).
      - updated: assignments seen before whose details (e.g. due date, description)
        were changed today by the lecturer.

    Moodle does not record when an assignment was created, so this tool remembers the
    assignments it has seen. On the very first run (first_run = true) it only records
    that baseline: "new" is empty and "updated" is based on today's changes only.
    Tell the user that new-assignment detection starts from that point.
    """
    return assignments.new_assignments(year)


@tool
def list_courses(semester: int | None = None, year: int | None = None) -> dict:
    """List the student's courses for an academic year, sorted by semester then name.

    Returns {"courses": [...]}. Each item has: id (Moodle course id, used by other
    course tools), name, course_number (the university's course number, e.g. 592), semester (1 or 2) and url.

    semester: 1 or 2 to return only that semester; omit for the whole year.
    Credit points, syllabus and class schedule are not stored in Moodle.
    """
    return {"courses": courses.list_courses(semester, year)}


@tool
def get_course_staff(course_id: int, year: int | None = None) -> dict:
    """The lecturer(s) and TAs of a course. course_id comes from list_courses.

    Returns {"staff": [{"id", "name", "role"}]} with role "lecturer" or "TA", lecturers first.
    Email addresses are not visible to students.
    """
    return {"staff": courses.get_course_staff(course_id, year)}


@tool
def get_course_contents(course_id: int, year: int | None = None) -> dict:
    """Everything posted on a course page, section by section (e.g. "Week 1", "Homeworks").

    Returns {"sections": [{"section", "summary"?, "items": [...]}]}. Each item has id,
    type, name and url, plus: files [{filename, url}] for uploaded files (slides, recitations,
    solutions), link for external links (e.g. Panopto recordings) and description
    when the lecturer wrote one. Common types: resource (file), assign, forum, url,
    page, folder, quiz, lti (Zoom/Panopto). course_id comes from list_courses.
    """
    return {"sections": courses.get_course_contents(course_id, year)}


@tool
def get_grades(course_id: int | None = None, year: int | None = None) -> dict:
    """The student's grades.

    Without course_id: {"courses": [{course_id, course, grade}]}, the current overall
    grade in every course (null = no grade yet).
    With course_id: {"course_id", "total", "items": [{name, grade, range, weight,
    feedback?}]}, every grade item in that course. grade null = not graded yet;
    weight is the item's share of the final grade. Items worth 0 % (e.g. attendance,
    alternative exam dates) do not count toward the total.
    """
    return grades.get_grades(course_id, year)


@tool
def staff_messages(days: int = 7, course_id: int | None = None, year: int | None = None) -> dict:
    """What lecturers and TAs posted or sent in the last `days` days, newest first.

    Returns {"messages": [...]}. Each item has kind, author, role ("lecturer" / "TA"),
    time and text, plus:
      - "announcement": a post on a course's announcement board (course, forum, subject, url)
      - "forum_reply": a staff answer in a Q&A forum; in_reply_to holds the student's question
      - "forum_post": a new staff discussion in a Q&A forum
      - "direct_message": a private Moodle message to the student (only when course_id is omitted)
    Long texts are cut at 2000 characters; the url opens the full post.

    course_id (from list_courses) limits it to one course and is faster.
    Takes a couple of seconds for a week across all courses; large windows are slower (a year ~15 s).
    """
    return {"messages": messages.staff_messages(days, course_id, year)}


@tool
def upcoming_deadlines(days: int = 14, include_overdue: bool = False, year: int | None = None) -> dict:
    """Things due in the next `days` days that still need action (Moodle's timeline),
    across all courses: assignments not yet submitted, quizzes not yet attempted, etc.

    Returns {"deadlines": [...]}. Each item has name, type (assign, quiz, ...), course,
    due, overdue, action (what to do, e.g. "Add submission") and url. Fast: one request.
    Use this for "what do I need to submit?" / "what's due soon?"; prefer it over
    list_assignments(status="pending"). Exams, moed B dates and other non-actionable
    events are not here: use calendar_events for those.
    include_overdue also returns items past due in the last 30 days.
    """
    return {"deadlines": deadlines.upcoming_deadlines(days, include_overdue, year)}


@tool
def calendar_events(days: int = 30, course_id: int | None = None, year: int | None = None) -> dict:
    """Everything on the student's Moodle calendar in the next `days` days, soonest first:
    exams, moed A/B dates, lectures or makeup classes the lecturer added, course and
    site-wide events, personal events, and activity dates (assignment due, quiz
    open/close), whether or not they need action.

    Use this for "when is my exam?", "when is moed B?", "what's happening this week?".
    For "what do I still need to submit?" use upcoming_deadlines instead: it knows what
    is already done, this tool does not.

    Returns {"events": [...]}. Each item has name, course (null for site and personal
    events), type ("course", "site", "user", "group", "category", or for activity dates
    "due", "open", "close", "gradingdue", ...), start and end ("YYYY-MM-DD HH:MM"; end
    null when the event has no duration) and url (the calendar day in Moodle), plus
    activity (assign, quiz, ...) for activity dates, location and description (plain
    text, cut at 500 characters) when set.
    Exams are usually course events named e.g. "מבחן" / "Exam" / "מועד ב", or quiz dates.

    course_id (from list_courses) returns only that course's events. Two requests.
    """
    return {"events": calendar.calendar_events(days, course_id, year)}


@tool
def search_moodle(query: str, page: int = 0, year: int | None = None) -> dict:
    """Moodle's site-wide search across the student's courses: forum posts, course
    sections, activities and files (by name).

    Returns {"total", "page", "results": [{title, kind, course, snippet, modified, url}]}.
    kind is "<component>/<area>", e.g. "mod_forum/post". Use page for more results.
    Search matches words, so try the language the course uses (Hebrew or English).
    """
    return search.search(query, page, year)


@tool
def read_content(url: str, offset: int = 0) -> dict:
    """Read the text of a course file or Page activity, e.g. lecture slides,
    exercise sheets, solutions, notebooks, code, or a "Page" with links.

    url: a file url (".../pluginfile.php/...") from get_course_contents or get_assignment,
    or a Page url (".../mod/page/view.php?id=..."). Only links to the student's own
    Moodle site are accepted.
    Returns {"name", "text", "total_chars", "next_offset"?}. Text is split with markers:
    "--- page N ---" (PDF), "--- slide N ---" (PowerPoint, speaker notes as "[notes]"),
    "--- cell N (type) ---" (Jupyter). Long texts come in parts of 30,000 characters:
    call again with offset=next_offset for the rest.
    Reads PDF, .pptx, .docx, .ipynb, text/code and HTML; not old .doc/.ppt, images or
    video. Text inside images (e.g. scanned PDFs, diagrams) is not extracted.
    """
    return reading.read_content(url, offset)


@tool
def exam_schedule(year: int | None = None, semester: int | None = None) -> dict:
    """The student's exam schedule (לוח בחינות) from Yedion, the university's student info
    station (not Moodle), sorted by date. Logs in with the student's university account on
    first use; two requests per call.

    Returns {"exams": [...]}. Each item: course, course_number (string), lecturer, semester,
    moed (1, 2, ... or "special" for מועד מיוחד), type (e.g. "מבחן סופי", "מבחן סופי - Campus"),
    date ("YYYY-MM-DD"), start ("HH:MM"), room (text, or null while not yet assigned; often
    "the location is published about an hour before the exam"), registered (true / false,
    null if the status is unrecognised), appeal_deadline ("YYYY-MM-DD" or null) and
    alternative_assessment: null for a normal exam, otherwise Yedion's text for the alternative
    assessment (e.g. a final project instead of an exam) - mention it, the student does not sit
    an exam in that course.

    year: academic year as in Moodle (2027 = Oct 2026 - Sep 2027, תשפ"ז); defaults to the
    current one by today's date (not MOODLE_DEFAULT_YEAR).
    semester: 1, 2, ... for one semester; omit (or 0) for the whole year.
    """
    return {"exams": exams.exam_schedule(year, semester)}


def main() -> None:
    """Run over stdio (default, for the Claude desktop app / Claude Code), or over HTTP
    when MCP_TRANSPORT=http (for hosting, e.g. on Render).

    In HTTP mode the endpoint is /<MCP_SECRET_PATH>/mcp. claude.ai custom connectors can't
    send a static auth header, so the unguessable path is what keeps the server private:
    any other path returns 404. Keep MCP_SECRET_PATH out of git (set it on the host)."""
    import os

    if os.environ.get("MCP_TRANSPORT", "stdio").lower() != "http":
        mcp.run()
        return

    secret = os.environ.get("MCP_SECRET_PATH", "").strip("/")
    if len(secret) < 32:
        raise SystemExit("MCP_SECRET_PATH must be set to a random string of at least 32 characters")

    import uvicorn

    from moodle_mcp.oauth import OAuth

    oauth = OAuth(secret)  # auto-approving sign-in that claude.ai requires; see oauth.py
    path = f"/{secret}/mcp"
    inner = mcp.streamable_http_app(
        streamable_http_path=path,
        stateless_http=True,  # no per-client session state, so restarts/sleeps don't break clients
        json_response=True,
        host="0.0.0.0",  # not localhost, so the SDK's localhost-only Host check stays off
    )

    async def app(scope, receive, send):
        if scope["type"] == "http" and oauth.handles(scope["path"]):
            await oauth(scope, receive, send)
            return
        # This server never pushes messages, so answer the optional GET listening stream with
        # 405 right away (allowed by the MCP spec) instead of holding the stream open until it
        # times out.
        if scope["type"] == "http" and scope["method"] in ("GET", "HEAD") and scope["path"] == path:
            await send({"type": "http.response.start", "status": 405,
                        "headers": [(b"allow", b"POST, DELETE"), (b"content-length", b"0")]})
            await send({"type": "http.response.body", "body": b""})
            return
        await inner(scope, receive, send)

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))  # Render/Cloud Run set PORT


if __name__ == "__main__":
    main()
