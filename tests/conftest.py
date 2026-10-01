"""Shared test setup: fake config and a fake Moodle web-service endpoint.

config.py reads the environment when it is imported, so the env vars are set here,
before any moodle_mcp module is imported, and the real .env is never loaded.
"""
import os
from pathlib import Path
from urllib.parse import parse_qsl

import dotenv
import httpx
import pytest
import respx

dotenv.load_dotenv = lambda *args, **kwargs: False  # keep the real tokens in .env out of tests
os.environ.update({
    "MOODLE_BASE_URL": "https://moodle.test/",
    "MOODLE_TOKEN_2026": "token-2026",
    "MOODLE_TOKEN_2027": "token-2027",
    "MOODLE_DEFAULT_YEAR": "2026",
    "RUNI_USERNAME": "student",
    "RUNI_PASSWORD": "pw-SECRET",
})

from moodle_mcp import assignments, client, runi  # noqa: E402  (must come after the env setup)

USER_ID = 42


class FakeMoodle:
    """Answers web-service calls by wsfunction and records every request.

    moodle.on("core_x", {...})               fixed JSON answer
    moodle.on("core_x", lambda params: ...)  answer computed from the request params
    """

    def __init__(self):
        self.handlers = {"core_webservice_get_site_info": {"userid": USER_ID}}
        self.calls: list[dict] = []

    def on(self, wsfunction: str, response) -> None:
        self.handlers[wsfunction] = response

    def calls_to(self, wsfunction: str) -> list[dict]:
        return [c for c in self.calls if c["wsfunction"] == wsfunction]

    def respond(self, request: httpx.Request) -> httpx.Response:
        params = dict(parse_qsl(request.content.decode()))
        params["_url"] = str(request.url)
        self.calls.append(params)
        handler = self.handlers[params["wsfunction"]]  # KeyError = the test forgot to mock it
        return httpx.Response(200, json=handler(params) if callable(handler) else handler)


@pytest.fixture
def moodle(tmp_path, monkeypatch):
    fake = FakeMoodle()
    client.get_user_id.cache_clear()
    monkeypatch.setattr(assignments, "STATE_DIR", tmp_path / ".state")
    monkeypatch.setattr(client.time, "sleep", lambda seconds: None)
    # any request that is not to the fake endpoint fails the test instead of reaching the network
    with respx.mock(assert_all_called=False) as router:
        router.post(url__regex=r"^https://moodle\.test/\d{4}/webservice/rest/server\.php$").mock(side_effect=fake.respond)
        fake.router = router
        yield fake


# --- Yedion (My RUNI single sign-on) ---

FIXTURES = Path(__file__).parent / "fixtures"
SAML_RESPONSE = "SAML-SECRET"  # stands in for the real SAMLResponse, which identifies the student
LOGIN_PAGE = "<form id='auth_form' method='post'><input type='text' name='username'><input type='password' name='password'></form>"
MFA_PAGE = "<form id='auth_form' method='post'><input type='password' name='otp'></form>"
YEDION_HOME = '<button data-progname="MenuCall" data-arguments="-N,-N,-N97," id="ExitStudent">יציאה</button>'


class FakeRuni:
    """My RUNI login (F5), the SAML hop and Yedion, with cookie sessions.

    runi_site.pages[PRGNAME] = html   what Yedion returns for a program
    runi_site.posts                   form data of every fireflyweb.aspx POST
    runi_site.password_posts          how many times the password was sent
    runi_site.expire()                drop Yedion's sessions (as if they timed out)
    runi_site.after_password = "mfa"  answer the password with a second-factor page
    runi_site.accepted_password       change it to make the configured password wrong
    """

    def __init__(self):
        self.pages: dict[str, str] = {}
        self.posts: list[dict] = []
        self.password_posts = 0
        self.after_password = "ok"
        self.accepted_password = os.environ["RUNI_PASSWORD"]
        self.saml_action = "https://yedion.runi.ac.il/yedion/login.aspx"
        self.saml_posts: list[str] = []
        self.sessions: set[str] = set()

    def expire(self):
        self.sessions.clear()

    def _yedion_session(self, request):
        cookies = dict(c.strip().split("=", 1) for c in request.headers.get("cookie", "").split(";") if "=" in c)
        return cookies.get("Yedion.MySession") in self.sessions

    def myruni_app(self, request):
        if "MRHSession=SESSION-SECRET" in request.headers.get("cookie", ""):
            return httpx.Response(200, text="<title>My RUNI</title>")
        return httpx.Response(302, headers={"Location": "/my.policy"})

    def policy_post(self, request):
        self.password_posts += 1
        form = dict(parse_qsl(request.content.decode()))
        if form.get("password") != self.accepted_password:
            return httpx.Response(200, text=LOGIN_PAGE)
        if self.after_password == "mfa":
            return httpx.Response(200, text=MFA_PAGE)
        return httpx.Response(302, headers={"Location": "/myruni/app/index.html",
                                            "Set-Cookie": "MRHSession=SESSION-SECRET; path=/"})

    def saml_idp(self, request):
        return httpx.Response(200, text=(
            f'<form action="{self.saml_action}" method="post">'
            f'<input type="hidden" name="SAMLResponse" value="{SAML_RESPONSE}"/>'
            '<input type="hidden" name="RelayState" value="relay"/><input type="submit" value="Continue"/></form>'))

    def yedion_login(self, request):
        form = dict(parse_qsl(request.content.decode()))
        self.saml_posts.append(form.get("SAMLResponse"))
        if form.get("SAMLResponse") != SAML_RESPONSE:
            return httpx.Response(200, text="anonymous")
        session = f"y{len(self.saml_posts)}"
        self.sessions.add(session)
        return httpx.Response(302, headers={"Location": "/yedion/fireflyweb.aspx?prgname=Main",
                                            "Set-Cookie": f"Yedion.MySession={session}; path=/"})

    def firefly_get(self, request):
        return httpx.Response(200, text=YEDION_HOME if self._yedion_session(request) else "anonymous")

    def firefly_post(self, request):
        if not self._yedion_session(request):  # Yedion sends logged-out users to the My RUNI login
            return httpx.Response(302, headers={"Location": "https://my.runi.ac.il/my.policy"})
        form = dict(parse_qsl(request.content.decode()))
        self.posts.append(form)
        return httpx.Response(200, text=self.pages[form["PRGNAME"]])  # KeyError = page not set up


@pytest.fixture
def runi_site(monkeypatch):
    """A fake My RUNI + Yedion; runi.py starts logged out. Unmocked requests fail the test."""
    monkeypatch.setattr(runi, "_client", None)
    monkeypatch.setattr(runi, "_generation", 0)
    monkeypatch.setattr(runi, "_login_failure", None)
    fake = FakeRuni()
    with respx.mock(assert_all_called=False) as router:
        router.get("https://my.runi.ac.il/myruni/app/index.html").mock(side_effect=fake.myruni_app)
        router.get("https://my.runi.ac.il/my.policy").mock(return_value=httpx.Response(200, text=LOGIN_PAGE))
        router.post("https://my.runi.ac.il/my.policy").mock(side_effect=fake.policy_post)
        router.get(url__regex=r"^https://yedion\.runi\.ac\.il/yedion/login\.aspx\?Type=S$").mock(
            return_value=httpx.Response(302, headers={"Location": "https://auth.runi.ac.il/saml/idp/profile/redirectorpost/sso?SAMLRequest=req"}))
        router.get(url__regex=r"^https://auth\.runi\.ac\.il/saml/").mock(side_effect=fake.saml_idp)
        router.post("https://yedion.runi.ac.il/yedion/login.aspx").mock(side_effect=fake.yedion_login)
        router.get(url__regex=r"^https://yedion\.runi\.ac\.il/yedion/fireflyweb\.aspx").mock(side_effect=fake.firefly_get)
        router.post("https://yedion.runi.ac.il/yedion/fireflyweb.aspx").mock(side_effect=fake.firefly_post)
        fake.router = router
        yield fake
