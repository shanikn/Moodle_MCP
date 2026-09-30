import httpx
import pytest

from moodle_mcp.client import MoodleError, _flatten, call, get_user_id
from moodle_mcp.config import get_site


def test_get_site_defaults_to_default_year():
    site = get_site()
    assert site.url == "https://moodle.test/2026"  # trailing slash in the base URL is stripped
    assert site.token == "token-2026"


def test_get_site_other_year():
    assert get_site(2027).url == "https://moodle.test/2027"
    assert get_site(2027).token == "token-2027"


def test_get_site_missing_year_explains_fix():
    with pytest.raises(ValueError, match="Add MOODLE_TOKEN_2030 to .env"):
        get_site(2030)


def test_flatten_expands_lists():
    assert _flatten({"courseids": [5, 7], "page": 0}) == {"courseids[0]": 5, "courseids[1]": 7, "page": 0}


def test_call_sends_token_format_and_params(moodle):
    moodle.on("core_x", {"ok": True})
    assert call("core_x", courseids=[1, 2]) == {"ok": True}
    sent = moodle.calls[-1]
    assert sent["wstoken"] == "token-2026"
    assert sent["moodlewsrestformat"] == "json"
    assert sent["moodlewssettingfilter"] == "true"
    assert (sent["courseids[0]"], sent["courseids[1]"]) == ("1", "2")


def test_call_uses_the_years_site_and_token(moodle):
    moodle.on("core_x", {})
    call("core_x", year=2027)
    assert moodle.calls[-1]["_url"].startswith("https://moodle.test/2027/")
    assert moodle.calls[-1]["wstoken"] == "token-2027"


def test_call_raises_moodle_error(moodle):
    moodle.on("core_x", {"exception": "moodle_exception", "errorcode": "invalidtoken", "message": "Invalid token"})
    with pytest.raises(MoodleError, match="invalidtoken: Invalid token"):
        call("core_x")


def test_call_retries_once_on_server_error(moodle):
    answers = iter([httpx.Response(502), httpx.Response(200, json={"ok": True})])
    moodle.router.routes[0].side_effect = lambda request: next(answers)
    assert call("core_x") == {"ok": True}


def test_call_gives_up_after_second_server_error(moodle):
    moodle.router.routes[0].side_effect = lambda request: httpx.Response(502)
    with pytest.raises(httpx.HTTPStatusError):
        call("core_x")


def test_get_user_id_is_cached_per_year(moodle):
    assert get_user_id() == 42
    assert get_user_id() == 42
    get_user_id(2027)
    assert len(moodle.calls_to("core_webservice_get_site_info")) == 2
