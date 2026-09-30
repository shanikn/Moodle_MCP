# the logic for reading the student's grades
from moodle_mcp.client import call, get_user_id
from moodle_mcp.courses import list_courses
from moodle_mcp.formatting import html_to_text


def _clean(value: str | None) -> str | None:
    value = html_to_text(value or "")
    return value if value and value != "-" else None


def get_grades(course_id: int | None = None, year: int | None = None) -> dict:
    user_id = get_user_id(year)
    if course_id is None:
        names = {c["id"]: c["name"] for c in list_courses(year=year)}
        overview = call("gradereport_overview_get_course_grades", year=year, userid=user_id)
        return {"courses": [
            {"course_id": g["courseid"], "course": names.get(g["courseid"]), "grade": _clean(g.get("grade"))}
            for g in overview["grades"]
        ]}

    report = call("gradereport_user_get_grade_items", year=year, courseid=course_id, userid=user_id)
    items, total = [], None
    for i in report["usergrades"][0]["gradeitems"]:
        if i.get("gradeishidden"):
            continue
        if i["itemtype"] == "course":
            total = _clean(i.get("gradeformatted"))
            continue
        items.append({
            "name": i.get("itemname") or "(category total)",
            "grade": _clean(i.get("gradeformatted")),
            "range": _clean(i.get("rangeformatted")),
            "weight": _clean(i.get("weightformatted")),
            **({"feedback": fb} if (fb := _clean(i.get("feedback"))) else {}),
        })
    return {"course_id": course_id, "total": total, "items": items}
