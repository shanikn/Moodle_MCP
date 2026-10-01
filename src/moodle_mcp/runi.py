# logs in to Yedion (the student info station) through My RUNI single sign-on and fetches its pages
#
# Login chain (F5 BIG-IP in front of My RUNI, SAML into Yedion):
#   1. GET  my.runi.ac.il/myruni/app/index.html -> 302 to /my.policy (login form)
#   2. POST /my.policy username, password, vhost=standard -> back to /myruni/app/index.html
#   3. GET  yedion/login.aspx?Type=S -> auth.runi.ac.il SAML IdP -> F5 SSO hops -> HTML form
#      with hidden SAMLResponse + RelayState
#   4. POST that form to yedion/login.aspx -> fireflyweb.aspx, logged in (cookie session)
#
# The password, the F5 cookies and the SAMLResponse identify the student: never log them,
# never put them (or URLs, which carry SSO tokens) in error messages.
import html
import logging
import os
import re
import threading
from urllib.parse import urlsplit

import httpx

# httpx logs every request URL at INFO, and SSO redirect URLs carry one-time tokens
logging.getLogger("httpx").setLevel(logging.WARNING)

MYRUNI_URL = "https://my.runi.ac.il/myruni/app/index.html"
YEDION_URL = "https://yedion.runi.ac.il/yedion/"
SSO_START_URL = YEDION_URL + "login.aspx?Type=S"
FIREFLY_URL = YEDION_URL + "fireflyweb.aspx"
# plain browser UA; don't add Accept: application/json / X-Requested-With to the login
# requests: with them My RUNI answers every later request with a 502
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
LOGGED_IN_MARKER = 'id="ExitStudent"'  # the "יציאה" (log out) button on every logged-in page


class RuniError(Exception):
    """Login or page fetch failed. Messages are safe to show: no credentials, cookies or URLs."""


_lock = threading.Lock()
_client: httpx.Client | None = None  # logged-in session; replaced (not cleared) on re-login
_generation = 0                      # bumped on every login, so racing threads re-login once
_login_failure: str | None = None    # set when the credentials were refused: never try again


def _where(response: httpx.Response) -> str:
    """host + path of a response, without the query string (it can carry SSO tokens)."""
    return f"{response.url.host}{response.url.path}"


def _is_logged_in(response: httpx.Response) -> bool:
    return response.url.host == "yedion.runi.ac.il" and LOGGED_IN_MARKER in response.text


def _saml_form(response: httpx.Response) -> tuple[str, dict]:
    """The IdP's auto-submit form: (action, {"SAMLResponse": ..., "RelayState": ...})."""
    action = re.search(r'<form[^>]*action="([^"]+)"', response.text)
    fields = dict(re.findall(r'<input[^>]*name="(SAMLResponse|RelayState)"[^>]*value="([^"]*)"', response.text))
    if not action or "SAMLResponse" not in fields:
        raise RuniError(f"Yedion single sign-on did not return a SAML response (stopped at {_where(response)}).")
    action_url = html.unescape(action.group(1))
    # the SAMLResponse identifies the student: only ever hand it to Yedion
    if not action_url.startswith(YEDION_URL):
        raise RuniError(f"Yedion single sign-on wants to post to an unexpected site ({urlsplit(action_url).netloc}).")
    return action_url, {k: html.unescape(v) for k, v in fields.items()}


def _login() -> httpx.Client:
    """Run the whole login chain on a new client (no old cookies). Raises RuniError when the
    university refuses the login or shows an unexpected page (e.g. MFA), httpx.HTTPError on
    network problems."""
    username = os.environ.get("RUNI_USERNAME")
    password = os.environ.get("RUNI_PASSWORD")
    if not username or not password:
        raise RuniError("Yedion login is not configured: set RUNI_USERNAME and RUNI_PASSWORD.")

    client = httpx.Client(follow_redirects=True, timeout=30, headers={"User-Agent": USER_AGENT})
    response = client.get(MYRUNI_URL)
    response.raise_for_status()
    if response.url.path != "/my.policy" or "name='password'" not in response.text:
        raise RuniError(f"My RUNI did not show its login form (got {_where(response)}).")

    response = client.post(str(response.url), data={"username": username, "password": password, "vhost": "standard"})
    response.raise_for_status()
    if "name='password'" in response.text:
        raise RuniError("My RUNI refused the username or password (or the account is locked). "
                        "Not retrying, to avoid locking the account: fix RUNI_USERNAME / RUNI_PASSWORD "
                        "and restart the server.")
    if response.url.host != "my.runi.ac.il" or not response.url.path.startswith("/myruni/app"):
        raise RuniError(f"My RUNI login stopped at an unexpected page ({_where(response)}), "
                        "possibly a second-factor (MFA) or access-blocked page.")

    response = client.get(SSO_START_URL)
    response.raise_for_status()
    action, fields = _saml_form(response)
    response = client.post(action, data=fields)
    response.raise_for_status()
    if not _is_logged_in(response):
        raise RuniError(f"Yedion did not accept the single sign-on (ended at {_where(response)}).")
    return client


def _ensure_login(seen_generation: int | None) -> tuple[httpx.Client, int]:
    """Return the current session, logging in if there is none or if the caller's session
    (seen_generation) expired and no other thread has replaced it yet."""
    global _client, _generation, _login_failure
    with _lock:
        if _login_failure:
            raise RuniError(_login_failure)
        if _client is None or _generation == seen_generation:
            try:
                _client = _login()
            except RuniError as exc:
                _login_failure = str(exc)  # the university said no: don't ask again with the same password
                raise
            _generation += 1
        return _client, _generation


def fetch(prgname: str, arguments: str, **fields) -> str:
    """POST a Yedion program (PRGNAME + ARGUMENTS, plus any form fields) and return the page HTML.

    Logs in on first use. If the session has expired, logs in again once and retries; a
    refused login is never retried."""
    data = {"PRGNAME": prgname, "ARGUMENTS": arguments, **fields}
    try:
        client, generation = _ensure_login(None)
        response = client.post(FIREFLY_URL, data=data)
        response.raise_for_status()
        if _is_logged_in(response):
            return response.text
        client, _ = _ensure_login(generation)  # session expired
        response = client.post(FIREFLY_URL, data=data)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        # str(exc) can include a URL with SSO tokens; report only the error type
        raise RuniError(f"Could not reach Yedion / My RUNI ({type(exc).__name__}).") from None
    if not _is_logged_in(response):
        raise RuniError(f"Yedion logged us out again right after logging in (got {_where(response)}).")
    return response.text
