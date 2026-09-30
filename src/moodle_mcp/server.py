from typing import Literal
from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from moodle_mcp import assignments, courses, deadlines, grades, messages, reading, search

mcp = MCPServer(
    "moodle",
    instructions=("Access to a student's Reichman University Moodle. Each academic year is a separate site; "
    "tools default to the current year unless 'year' is given. Dates are local Israel time."),
)

READ_ONLY = ToolAnnotations(read_only_hint=True)

@mcp.tool(annotations=READ_ONLY)
def list_assignments(status: Literal["all", "pending","submitted"] = "all",
                     include_overdue: bool = False,
                     year: int | None = None) -> list[dict]:
    """List the student's assignments across all their courses, sorted by due date.

    Each item has: id, name, course, due, cutoff (dates as "YYYY-MM-DD HH:MM" or null),
    url (link to the assignment in Moodle) and timemodified. With a status filter,
    each item also has status: "new" (nothing handed in), "draft" (uploaded but not
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
    return assignments.list_assignments(status, include_overdue, year)


@mcp.tool(annotations=READ_ONLY)
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


@mcp.tool(annotations=READ_ONLY)
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


@mcp.tool(annotations=READ_ONLY)
def list_courses(semester: int | None = None, year: int | None = None) -> list[dict]:
    """List the student's courses for an academic year, sorted by semester then name.

    Each item has: id (Moodle course id, used by other course tools), name,
    course_number (the university's course number, e.g. 592), semester (1 or 2) and url.

    semester: 1 or 2 to return only that semester; omit for the whole year.
    Credit points, syllabus and class schedule are not stored in Moodle.
    """
    return courses.list_courses(semester, year)


@mcp.tool(annotations=READ_ONLY)
def get_course_staff(course_id: int, year: int | None = None) -> list[dict]:
    """The lecturer(s) and TAs of a course. course_id comes from list_courses.

    Returns [{"id", "name", "role"}] with role "lecturer" or "TA", lecturers first.
    Email addresses are not visible to students.
    """
    return courses.get_course_staff(course_id, year)


@mcp.tool(annotations=READ_ONLY)
def get_course_contents(course_id: int, year: int | None = None) -> list[dict]:
    """Everything posted on a course page, section by section (e.g. "Week 1", "Homeworks").

    Returns [{"section", "summary"?, "items": [...]}]. Each item has id, type, name and
    url, plus: files [{filename, url}] for uploaded files (slides, recitations,
    solutions), link for external links (e.g. Panopto recordings) and description
    when the lecturer wrote one. Common types: resource (file), assign, forum, url,
    page, folder, quiz, lti (Zoom/Panopto). course_id comes from list_courses.
    """
    return courses.get_course_contents(course_id, year)


@mcp.tool(annotations=READ_ONLY)
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


@mcp.tool(annotations=READ_ONLY)
def staff_messages(days: int = 7, course_id: int | None = None, year: int | None = None) -> list[dict]:
    """What lecturers and TAs posted or sent in the last `days` days, newest first.

    Each item has kind, author, role ("lecturer" / "TA"), time and text, plus:
      - "announcement": a post on a course's announcement board (course, forum, subject, url)
      - "forum_reply": a staff answer in a Q&A forum; in_reply_to holds the student's question
      - "forum_post": a new staff discussion in a Q&A forum
      - "direct_message": a private Moodle message to the student (only when course_id is omitted)
    Long texts are cut at 2000 characters; the url opens the full post.

    course_id (from list_courses) limits it to one course and is faster.
    Takes a couple of seconds for a week across all courses; large windows are slower (a year ~15 s).
    """
    return messages.staff_messages(days, course_id, year)


@mcp.tool(annotations=READ_ONLY)
def upcoming_deadlines(days: int = 14, include_overdue: bool = False, year: int | None = None) -> list[dict]:
    """Things due in the next `days` days that still need action (Moodle's timeline),
    across all courses: assignments not yet submitted, quizzes not yet attempted, etc.

    Each item has name, type (assign, quiz, ...), course, due, overdue, action (what to do,
    e.g. "Add submission") and url. Fast: one request. Prefer this over
    list_assignments(status="pending") for "what's due soon?" questions.
    include_overdue also returns items past due in the last 30 days.
    """
    return deadlines.upcoming_deadlines(days, include_overdue, year)


@mcp.tool(annotations=READ_ONLY)
def search_moodle(query: str, page: int = 0, year: int | None = None) -> dict:
    """Moodle's site-wide search across the student's courses: forum posts, course
    sections, activities and files (by name).

    Returns {"total", "page", "results": [{title, kind, course, snippet, modified, url}]}.
    kind is "<component>/<area>", e.g. "mod_forum/post". Use page for more results.
    Search matches words, so try the language the course uses (Hebrew or English).
    """
    return search.search(query, page, year)


@mcp.tool(annotations=READ_ONLY)
def read_content(url: str, offset: int = 0) -> dict:
    """Read the text of a course file or Page activity, e.g. lecture slides as PDF,
    exercise sheets, solutions, or a "Page" with links.

    url: a file url (".../pluginfile.php/...") from get_course_contents or get_assignment,
    or a Page url (".../mod/page/view.php?id=..."). Only links to the student's own
    Moodle site are accepted.
    Returns {"name", "text", "total_chars", "next_offset"?}. PDF text is split with
    "--- page N ---" markers. Long texts come in parts of 30,000 characters: call again
    with offset=next_offset for the rest.
    Reads PDF, text and HTML; not .pptx/.docx or images (look for a PDF version).
    """
    return reading.read_content(url, offset)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
