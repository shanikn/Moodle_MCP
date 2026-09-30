# Moodle MCP

An MCP server that gives Claude read access to a student's Moodle account
(Reichman University, `moodle.runi.ac.il`), using the same web-service API as the Moodle mobile app.
No admin rights needed.

> **Status:** work in progress. Phases 1–3 (assignments, courses, grades, staff messages) work and are covered by tests; Phase 4 (deadlines, reading, search) is next.

## Planned tools

**Phase 1 – Assignments**

| Tool | Description | Moodle API |
|---|---|---|
| ✅ `list_assignments` | Assignments across your courses, with due dates. `status`: `all` (default) / `pending` (not submitted, incl. drafts) / `submitted`; `include_overdue` (default off) | `mod_assign_get_assignments` + `mod_assign_get_submission_status` per assignment |
| ✅ `new_assignments` | Assignments added (not in last snapshot) or updated today (`timemodified`) | `mod_assign_get_assignments` + local snapshot |
| ✅ `get_assignment` | One assignment's details, submission status and feedback | `mod_assign_get_submission_status` |

**Phase 2 – Courses**

| Tool | Description | Moodle API |
|---|---|---|
| ✅ `list_courses` | Your courses, with semester and course number | `core_enrol_get_users_courses`, `core_course_get_courses_by_field` |
| ✅ `get_course_staff` | Lecturer (`editingteacher`) and TAs (`tutor`, `instruction_assistant`) | `core_enrol_get_enrolled_users` |
| ✅ `get_course_contents` | Sections and activities in a course | `core_course_get_contents` |
| ✅ `get_grades` | With a course: each grade item, grade and weight. Without: overall grade per course | `gradereport_user_get_grade_items` (needs `userid`), `gradereport_overview_get_course_grades` |

**Phase 3 – Communication**

| Tool | Description | Moodle API |
|---|---|---|
| ✅ `staff_messages` | Announcements and Q&A answers by lecturers/TAs, and direct messages, from the last N days | `mod_forum_*`, `core_enrol_get_enrolled_users`, `core_message_get_conversation_messages` |

**Phase 4 – Reading & schedule**

| Tool | Description | Moodle API |
|---|---|---|
| `upcoming_deadlines` | Assignments and quizzes due soon | `core_calendar_get_action_events_by_timesort` |
| `read_page` | Text of a Page activity or course file (PDF, etc.) | `mod_page_get_pages_by_courses` + file download |
| `search` | Moodle global search across your courses | `core_search_get_results` |

**Later / optional:** write actions (e.g. submitting an assignment).

**Not available in Moodle:** syllabus, credit points and class schedule. These live in the
university's own systems and would need a separate data source.

Every tool takes an optional `year` (defaults to `MOODLE_DEFAULT_YEAR`).
All API functions available to a student token: [docs/moodle_functions.md](docs/moodle_functions.md).

## Setup

Requires [uv](https://docs.astral.sh/uv/) and Python 3.13+.

```
uv sync
```

Create `.env` in the project root (it is git-ignored):

```
MOODLE_BASE_URL=https://moodle.runi.ac.il
MOODLE_TOKEN_2026=<token>
MOODLE_TOKEN_2027=<token>
MOODLE_DEFAULT_YEAR=2026
```

Each academic year is a separate Moodle site (`<base>/<year>`) with its own token.
Add a `MOODLE_TOKEN_<year>` line per year; no code changes needed.

### Getting a token (SSO login)

1. Log in to `https://moodle.runi.ac.il/<year>` in your browser.
2. Open DevTools (F12) → Network → enable *Preserve log*.
3. Visit:
   `https://moodle.runi.ac.il/<year>/admin/tool/mobile/launch.php?service=moodle_mobile_app&passport=12345&urlscheme=moodlemobile`
4. The page redirects to `moodlemobile://token=<base64>`. Base64-decode it; the result is
   `<signature>:::<token>`. Use the part after `:::`.

Treat the token like a password. To revoke it, log out of the Moodle app or remove it under
*Preferences → Security keys*.

## Tests

```
uv run pytest
```

Runs against a fake Moodle (no network, no real tokens).

## Connect to Claude Code

```
claude mcp add moodle -- uv run --directory <path-to-this-repo> moodle-mcp
```

## Project layout

```
src/moodle_mcp/
  config.py       # reads .env, resolves site URL + token per year
  client.py       # calls the Moodle REST API
  assignments.py  # assignment listing + new-assignment detection
  server.py       # FastMCP tool definitions
docs/
  moodle_functions.md  # API functions available to the token
```
