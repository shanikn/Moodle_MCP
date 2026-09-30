# the logic for listing the student's courses
import re

from moodle_mcp.client import call, get_user_id
from moodle_mcp.config import get_site

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
