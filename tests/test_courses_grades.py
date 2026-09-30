from moodle_mcp.courses import get_course_contents, get_course_staff, list_courses
from moodle_mcp.grades import get_grades
from tests.conftest import USER_ID


def enrolled(*courses):
    return [{"id": id, "fullname": name, "shortname": short} for id, name, short in courses]


COURSES = enrolled(
    (11, "Computer Networks", "Computer Networks-592-2026/1 - 11"),
    (12, "Algorithmic Game Theory", "תורת המשחקים-3987-2026/2 - 12"),
    (13, "Orientation", "orientation"),  # does not follow the pattern
)


def test_list_courses_parses_number_and_semester(moodle):
    moodle.on("core_enrol_get_users_courses", COURSES)
    result = list_courses()
    assert result[0] == {"id": 11, "name": "Computer Networks", "course_number": 592, "semester": 1,
                         "url": "https://moodle.test/2026/course/view.php?id=11"}
    assert [(c["id"], c["semester"]) for c in result] == [(11, 1), (12, 2), (13, None)]
    assert moodle.calls_to("core_enrol_get_users_courses")[0]["userid"] == str(USER_ID)


def test_list_courses_semester_filter(moodle):
    moodle.on("core_enrol_get_users_courses", COURSES)
    assert [c["id"] for c in list_courses(semester=2)] == [12]


def test_course_staff_maps_roles(moodle):
    def role(*names):
        return [{"shortname": n} for n in names]
    moodle.on("core_enrol_get_enrolled_users", [
        {"id": 1, "fullname": "Student", "roles": role("student")},
        {"id": 2, "fullname": "Guest", "roles": role("idcguest")},
        {"id": 3, "fullname": "Zoe TA", "roles": role("tutor")},
        {"id": 4, "fullname": "Amir TA", "roles": role("instruction_assistant")},
        {"id": 5, "fullname": "Prof", "roles": role("editingteacher", "instruction_assistant")},
    ])
    assert get_course_staff(11) == [
        {"id": 5, "name": "Prof", "role": "lecturer"},
        {"id": 4, "name": "Amir TA", "role": "TA"},
        {"id": 3, "name": "Zoe TA", "role": "TA"},
    ]
    # only the fields we need are requested
    assert moodle.calls[-1]["options[0][value]"] == "id,fullname,roles"


def test_course_contents_shapes_sections(moodle):
    moodle.on("core_course_get_contents", [
        {"name": "General", "summary": "", "modules": []},  # empty: dropped
        {"name": "Week 1", "summary": "<p>Intro</p>", "modules": [
            {"id": 1, "modname": "resource", "name": "Slides", "url": "u1",
             "contents": [{"filename": "l1.pdf", "fileurl": "https://moodle.test/2026/webservice/pluginfile.php/l1.pdf"}]},
            {"id": 2, "modname": "url", "name": "Recording", "url": "u2",
             "contents": [{"filename": "rec", "fileurl": "https://panopto.test/rec"}]},
            {"id": 3, "modname": "assign", "name": "Hidden", "url": "u3", "uservisible": False},
            {"id": 4, "modname": "forum", "name": "Q&A", "url": "u4", "description": "<p>Ask here</p>"},
        ]},
    ])
    assert get_course_contents(11) == [{"section": "Week 1", "summary": "Intro", "items": [
        {"id": 1, "type": "resource", "name": "Slides", "url": "u1",
         "files": [{"filename": "l1.pdf", "url": "https://moodle.test/2026/pluginfile.php/l1.pdf"}]},
        {"id": 2, "type": "url", "name": "Recording", "url": "u2", "link": "https://panopto.test/rec"},
        {"id": 4, "type": "forum", "name": "Q&A", "url": "u4", "description": "Ask here"},
    ]}]


def test_grades_overview_names_courses(moodle):
    moodle.on("core_enrol_get_users_courses", COURSES)
    moodle.on("gradereport_overview_get_course_grades", {"grades": [
        {"courseid": 11, "grade": "9.60"}, {"courseid": 12, "grade": "-"},
    ]})
    assert get_grades() == {"courses": [
        {"course_id": 11, "course": "Computer Networks", "grade": "9.60"},
        {"course_id": 12, "course": "Algorithmic Game Theory", "grade": None},
    ]}


def test_grades_for_course(moodle):
    moodle.on("gradereport_user_get_grade_items", {"usergrades": [{"gradeitems": [
        {"itemtype": "mod", "itemname": "Homework 1", "gradeformatted": "48.00",
         "rangeformatted": "0&ndash;100", "weightformatted": "20.00 %", "feedback": "<p>Good</p>"},
        {"itemtype": "mod", "itemname": "Homework 2", "gradeformatted": "-",
         "rangeformatted": "0&ndash;100", "weightformatted": "20.00 %", "feedback": ""},
        {"itemtype": "manual", "itemname": "Secret", "gradeishidden": True, "gradeformatted": "1"},
        {"itemtype": "course", "itemname": None, "gradeformatted": "9.60"},
    ]}]})
    result = get_grades(11)
    assert result["total"] == "9.60"
    assert result["items"] == [
        {"name": "Homework 1", "grade": "48.00", "range": "0–100", "weight": "20.00 %", "feedback": "Good"},
        {"name": "Homework 2", "grade": None, "range": "0–100", "weight": "20.00 %"},
    ]
    assert moodle.calls_to("gradereport_user_get_grade_items")[0]["userid"] == str(USER_ID)
