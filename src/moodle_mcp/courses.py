# the logic for listing the student's courses
import re

from moodle_mcp.client import call, get_user_id
from moodle_mcp.config import get_site
from moodle_mcp.formatting import file_list, html_to_text

# RUNI short names look like "Computer Networks-592-2026/1 - 2601137":
# <name>-<course number>-<year>/<semester> - <moodle id>
SHORTNAME = re.compile(r"-(\d+)-\d{4}/(\d+)\s*-\s*\d+$")


def list_courses(semester: int | None = None, year: int | None = None) -> list[dict]:
    site = get_site(year)
    courses = []
    for c in call("core_enrol_get_users_courses", year=year, userid=get_user_id(year)):
        match = SHORTNAME.search(c["shortname"])
        course = {
            "id": c["id"],
            "name": c["fullname"],
            "course_number": int(match.group(1)) if match else None,
            "semester": int(match.group(2)) if match else None,
            "url": f"{site.url}/course/view.php?id={c['id']}",
        }
        if semester is None or course["semester"] == semester:
            courses.append(course)
    courses.sort(key=lambda x: (x["semester"] or 99, x["name"]))
    return courses


# RUNI role short names -> what the student would call them.
# Other roles (student, idcguest, student_site_sec, ...) are not course staff.
STAFF_ROLES = {"editingteacher": "lecturer", "teacher": "lecturer", "tutor": "TA", "instruction_assistant": "TA"}


def get_course_staff(course_id: int, year: int | None = None) -> list[dict]:
    users = call(
        "core_enrol_get_enrolled_users", year=year, courseid=course_id,
        # only fetch what we need; a course can have hundreds of students
        **{"options[0][name]": "userfields", "options[0][value]": "id,fullname,roles"},
    )
    staff = []
    for u in users:
        roles = {STAFF_ROLES[r["shortname"]] for r in u.get("roles", []) if r["shortname"] in STAFF_ROLES}
        if roles:
            # someone who is both lecturer and TA is listed as lecturer
            staff.append({"id": u["id"], "name": u["fullname"], "role": "lecturer" if "lecturer" in roles else "TA"})
    staff.sort(key=lambda s: (s["role"] != "lecturer", s["name"]))
    return staff


def get_course_contents(course_id: int, year: int | None = None) -> list[dict]:
    sections = []
    for s in call("core_course_get_contents", year=year, courseid=course_id):
        items = []
        for m in s["modules"]:
            if not m.get("uservisible", True):
                continue
            item = {"id": m["id"], "type": m["modname"], "name": m["name"], "url": m.get("url")}
            if description := html_to_text(m.get("description", "")):
                item["description"] = description
            if m["modname"] == "url":
                # link activities: contents[0].fileurl is the external link itself
                item["link"] = next((c["fileurl"] for c in m.get("contents", [])), None)
            elif files := file_list([{"files": m.get("contents", [])}]):
                item["files"] = files
            items.append(item)
        summary = html_to_text(s.get("summary", ""))
        if items or summary:
            sections.append({"section": s["name"], **({"summary": summary} if summary else {}), "items": items})
    return sections
