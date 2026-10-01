from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest

from moodle_mcp import runi
from tests.conftest import SAML_RESPONSE

SECRETS = ("pw-SECRET", "SESSION-SECRET", SAML_RESPONSE)


def assert_no_secrets(text: str):
    for secret in SECRETS:
        assert secret not in text


def test_logs_in_once_then_reuses_the_session(runi_site):
    runi_site.pages["MenuCall"] = runi_site.pages["Other"] = '<b id="ExitStudent">page</b>'
    assert "page" in runi.fetch("MenuCall", "-N,-N,-N6,-A")
    assert "page" in runi.fetch("Other", "-N1")
    assert runi_site.password_posts == 1
    assert runi_site.saml_posts == [SAML_RESPONSE]
    assert [(p["PRGNAME"], p["ARGUMENTS"]) for p in runi_site.posts] == [("MenuCall", "-N,-N,-N6,-A"), ("Other", "-N1")]


def test_expired_yedion_session_is_renewed_without_the_password(runi_site):
    runi_site.pages["MenuCall"] = '<b id="ExitStudent">page</b>'
    runi.fetch("MenuCall", "")
    runi_site.expire()
    assert "page" in runi.fetch("MenuCall", "")
    assert runi_site.events == ["password", "sso", "sso"]  # second SSO hop reuses the My RUNI session


def test_when_my_runi_expired_too_the_old_session_is_logged_out_before_the_password(runi_site):
    runi_site.pages["MenuCall"] = '<b id="ExitStudent">page</b>'
    runi.fetch("MenuCall", "")
    runi_site.expire()
    runi_site.expire_myruni()
    assert "page" in runi.fetch("MenuCall", "")
    assert runi_site.events == ["password", "sso", "sso-bounce", "logout", "password", "sso"]


def test_parallel_calls_on_an_expired_session_renew_it_only_once(runi_site):
    runi_site.pages["MenuCall"] = '<b id="ExitStudent">page</b>'
    runi.fetch("MenuCall", "")
    runi_site.expire()
    runi_site.expire_myruni()
    with ThreadPoolExecutor(8) as pool:
        pages = list(pool.map(lambda _: runi.fetch("MenuCall", ""), range(16)))
    assert all("page" in p for p in pages)
    assert runi_site.events == ["password", "sso", "sso-bounce", "logout", "password", "sso"]


def test_logged_out_again_right_after_renewal_is_an_error(runi_site):
    runi_site.pages["MenuCall"] = "<b>no logout button: looks logged out</b>"
    with pytest.raises(runi.RuniError, match="logged us out again"):
        runi.fetch("MenuCall", "")
    assert runi_site.events == ["password", "sso", "sso"]  # login + exactly one renewal


def test_password_logins_are_capped_per_hour(runi_site, monkeypatch):
    clock = [1000.0]
    monkeypatch.setattr(runi.time, "monotonic", lambda: clock[0])
    runi_site.pages["MenuCall"] = '<b id="ExitStudent">page</b>'
    for _ in range(runi.MAX_PASSWORD_LOGINS):
        runi_site.expire()
        runi_site.expire_myruni()
        runi.fetch("MenuCall", "")
        clock[0] += 60
    runi_site.expire()
    runi_site.expire_myruni()
    with pytest.raises(runi.RuniError, match="3 times in the last hour; refusing another login for about 58 minutes"):
        runi.fetch("MenuCall", "")
    assert runi_site.password_posts == 3

    clock[0] += 3600  # the cap is not remembered as a failure: an hour later logins work again
    assert "page" in runi.fetch("MenuCall", "")
    assert runi_site.password_posts == 4


def test_sso_bounce_right_after_password_is_not_retried(runi_site):
    runi_site.sso_bounces = True  # e.g. F5's limit of open sessions per user
    for _ in range(2):
        with pytest.raises(runi.RuniError, match="possibly too many open sessions") as exc:
            runi.fetch("MenuCall", "")
        assert_no_secrets(str(exc.value))
    assert runi_site.password_posts == 1


def test_refused_password_is_never_retried(runi_site):
    runi_site.accepted_password = "changed"
    for _ in range(3):
        with pytest.raises(runi.RuniError, match="refused the username or password") as exc:
            runi.fetch("MenuCall", "")
        assert_no_secrets(str(exc.value))
    assert runi_site.password_posts == 1  # later calls fail without sending the password again


def test_mfa_page_is_a_clear_error_and_is_not_retried(runi_site):
    runi_site.after_password = "mfa"
    for _ in range(2):
        with pytest.raises(runi.RuniError, match="MFA") as exc:
            runi.fetch("MenuCall", "")
        assert_no_secrets(str(exc.value))
    assert runi_site.password_posts == 1


def test_missing_credentials(runi_site, monkeypatch):
    monkeypatch.delenv("RUNI_PASSWORD")
    with pytest.raises(runi.RuniError, match="set RUNI_USERNAME and RUNI_PASSWORD"):
        runi.fetch("MenuCall", "")
    assert runi_site.password_posts == 0


def test_saml_response_is_only_posted_to_yedion(runi_site):
    runi_site.saml_action = "https://evil.example/collect"
    with pytest.raises(runi.RuniError, match="unexpected site") as exc:
        runi.fetch("MenuCall", "")
    assert_no_secrets(str(exc.value))
    assert runi_site.saml_posts == []  # unmocked evil.example would also have failed the test


def test_network_error_hides_urls_and_does_not_block_the_next_attempt(runi_site):
    route = runi_site.router.routes[0]
    route.side_effect = httpx.ConnectError("failed for https://auth.runi.ac.il/?TOKEN=SESSION-SECRET")
    with pytest.raises(runi.RuniError, match=r"Could not reach Yedion / My RUNI \(ConnectError\)") as exc:
        runi.fetch("MenuCall", "")
    assert_no_secrets(str(exc.value))
    assert exc.value.__cause__ is None and exc.value.__suppress_context__

    route.side_effect = runi_site.myruni_app  # network back: login is attempted again
    runi_site.pages["MenuCall"] = '<b id="ExitStudent">page</b>'
    assert "page" in runi.fetch("MenuCall", "")
