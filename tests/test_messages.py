import time

from moodle_mcp.messages import _active_discussions, staff_messages
from tests.conftest import USER_ID

NOW = int(time.time())
HOUR, DAY = 3600, 86400
LECTURER, TA, STUDENT = 7, 8, 50


def discussion(id, subject, author, author_name, created, modified=None, replies=0, pinned=False):
    return {"discussion": id, "subject": subject, "userid": author, "userfullname": author_name,
            "created": created, "timemodified": modified or created, "numreplies": replies,
            "pinned": pinned, "message": f"<p>{subject} text</p>"}


def post(id, author, name, created, parent=None, message="text"):
    return {"id": id, "author": {"id": author, "fullname": name}, "timecreated": created, "parentid": parent,
            "subject": f"post {id}", "message": f"<p>{message}</p>", "urls": {"view": f"https://moodle.test/p{id}"}}


def setup_course(moodle):
    moodle.on("core_enrol_get_users_courses", [
        {"id": 1, "fullname": "Networks", "shortname": "Networks-592-2026/1 - 1"},
        {"id": 2, "fullname": "Quiet course", "shortname": "Quiet-1-2026/1 - 2"},
    ])
    moodle.on("mod_forum_get_forums_by_courses", [
        {"id": 10, "course": 1, "type": "news", "name": "Announcements", "numdiscussions": 2},
        {"id": 11, "course": 1, "type": "general", "name": "HW questions", "numdiscussions": 1},
        {"id": 20, "course": 2, "type": "news", "name": "Announcements", "numdiscussions": 0},
    ])
    forums = {
        "10": [discussion(100, "HW 5 graded", LECTURER, "Prof", NOW - HOUR),
               discussion(101, "Welcome", LECTURER, "Prof", NOW - 30 * DAY)],
        "11": [discussion(110, "Q about HW", STUDENT, "Student", NOW - 2 * DAY, modified=NOW - HOUR, replies=2)],
    }
    moodle.on("mod_forum_get_forum_discussions", lambda p: {"discussions": forums[p["forumid"]]})
    moodle.on("mod_forum_get_discussion_posts", {"posts": [
        post(1, STUDENT, "Student", NOW - 2 * DAY, message="Is Q2 about TCP?"),
        post(2, TA, "Tal TA", NOW - HOUR, parent=1, message="Yes, TCP."),
        post(3, STUDENT + 1, "Other student", NOW - HOUR, parent=2),
    ]})
    moodle.on("core_enrol_get_enrolled_users", [
        {"id": LECTURER, "fullname": "Prof", "roles": [{"shortname": "editingteacher"}]},
        {"id": TA, "fullname": "Tal TA", "roles": [{"shortname": "tutor"}]},
        {"id": STUDENT, "fullname": "Student", "roles": [{"shortname": "student"}]},
    ])
    moodle.on("core_message_get_conversations", {"conversations": [
        {"id": 1, "members": [{"id": USER_ID, "fullname": "Me"}]},  # personal space, skipped
        {"id": 2, "members": [{"id": LECTURER, "fullname": "Prof"}]},
    ]})
    moodle.on("core_message_get_conversation_messages", {"messages": [
        {"useridfrom": LECTURER, "text": "<p>See me after class</p>", "timecreated": NOW - 2 * HOUR},
        {"useridfrom": USER_ID, "text": "<p>OK</p>", "timecreated": NOW - HOUR},
    ]})


def test_staff_messages_collects_announcements_replies_and_dms(moodle):
    setup_course(moodle)
    result = staff_messages(days=7)

    kinds = [(m["kind"], m["author"]) for m in result]
    assert sorted(kinds) == [("announcement", "Prof"), ("direct_message", "Prof"), ("forum_reply", "Tal TA")]

    announcement = next(m for m in result if m["kind"] == "announcement")
    assert announcement["role"] == "lecturer"
    assert announcement["text"] == "HW 5 graded text"
    assert announcement["url"] == "https://moodle.test/2026/mod/forum/discuss.php?d=100"

    reply = next(m for m in result if m["kind"] == "forum_reply")
    assert reply["role"] == "TA"
    assert reply["text"] == "Yes, TCP."
    assert reply["in_reply_to"] == "Is Q2 about TCP?"

    times = [m["time"] for m in result]
    assert times == sorted(times, reverse=True)


def test_staff_messages_skips_quiet_forums_and_courses(moodle):
    setup_course(moodle)
    staff_messages(days=7)
    # forum 20 has no discussions at all, so it is never asked for
    assert {c["forumid"] for c in moodle.calls_to("mod_forum_get_forum_discussions")} == {"10", "11"}
    # staff are only looked up for the course that had activity
    assert [c["courseid"] for c in moodle.calls_to("core_enrol_get_enrolled_users")] == ["1"]


def test_staff_messages_for_one_course_skips_direct_messages(moodle):
    setup_course(moodle)
    result = staff_messages(days=7, course_id=1)
    assert "direct_message" not in {m["kind"] for m in result}
    assert moodle.calls_to("core_message_get_conversations") == []


def test_long_text_is_cut(moodle):
    setup_course(moodle)
    moodle.on("mod_forum_get_forum_discussions", lambda p: {"discussions": [
        {**discussion(100, "Long", LECTURER, "Prof", NOW - HOUR), "message": "x" * 5000}] if p["forumid"] == "10" else []})
    text = staff_messages(days=7, course_id=1)[0]["text"]
    assert len(text) == 2002 and text.endswith(" …")


def test_active_discussions_pages_until_older_activity(moodle):
    pages = {
        "0": [discussion(i, "d", STUDENT, "S", NOW - HOUR) for i in range(10)],
        "1": [discussion(10, "d", STUDENT, "S", NOW - HOUR), discussion(11, "old", STUDENT, "S", NOW - 30 * DAY)],
    }
    moodle.on("mod_forum_get_forum_discussions", lambda p: {"discussions": pages[p["page"]]})
    active = _active_discussions({"id": 5}, since=NOW - 7 * DAY, year=None)
    assert len(active) == 11
    assert len(moodle.calls_to("mod_forum_get_forum_discussions")) == 2
