"""Shared test setup: fake config and a fake Moodle web-service endpoint.

config.py reads the environment when it is imported, so the env vars are set here,
before any moodle_mcp module is imported, and the real .env is never loaded.
"""
import os
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
})

from moodle_mcp import assignments, client  # noqa: E402  (must come after the env setup)

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
