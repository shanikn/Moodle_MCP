"""The auto-approving OAuth flow claude.ai runs when adding the server as a connector."""
import base64
import hashlib
from urllib.parse import parse_qs, urlsplit

from starlette.testclient import TestClient

from moodle_mcp.oauth import OAuth

SECRET = "s" * 40
CALLBACK = "https://claude.ai/api/mcp/auth_callback"


async def app(scope, receive, send):
    oauth = OAuth(SECRET)
    if oauth.handles(scope["path"]):
        await oauth(scope, receive, send)
    else:
        await send({"type": "http.response.start", "status": 404, "headers": []})
        await send({"type": "http.response.body", "body": b""})


client = TestClient(app, base_url="https://example.run.app")


def pkce():
    verifier = "v" * 50
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return verifier, challenge


def authorize(challenge, redirect_uri=CALLBACK):
    return client.get(f"/{SECRET}/authorize", params={
        "response_type": "code", "client_id": "c", "redirect_uri": redirect_uri,
        "code_challenge": challenge, "code_challenge_method": "S256", "state": "xyz",
    }, follow_redirects=False)


def test_discovery_points_to_secret_paths():
    prm = client.get(f"/.well-known/oauth-protected-resource/{SECRET}/mcp").json()
    assert prm["authorization_servers"] == [f"https://example.run.app/{SECRET}"]
    meta = client.get(f"/.well-known/oauth-authorization-server/{SECRET}").json()
    assert meta["token_endpoint"] == f"https://example.run.app/{SECRET}/token"


def test_root_discovery_does_not_leak_secret():
    for p in ["/.well-known/oauth-protected-resource", "/.well-known/oauth-authorization-server", "/register"]:
        assert client.get(p).status_code == 404


def test_full_flow_and_refresh():
    assert client.post(f"/{SECRET}/register", json={"redirect_uris": [CALLBACK]}).status_code == 201
    verifier, challenge = pkce()
    r = authorize(challenge)
    assert r.status_code == 302
    query = parse_qs(urlsplit(r.headers["location"]).query)
    assert query["state"] == ["xyz"]
    tokens = client.post(f"/{SECRET}/token", data={
        "grant_type": "authorization_code", "code": query["code"][0],
        "code_verifier": verifier, "redirect_uri": CALLBACK,
    }).json()
    assert tokens["token_type"] == "Bearer"
    refreshed = client.post(f"/{SECRET}/token", data={
        "grant_type": "refresh_token", "refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200


def test_wrong_pkce_verifier_rejected():
    _, challenge = pkce()
    code = parse_qs(urlsplit(authorize(challenge).headers["location"]).query)["code"][0]
    r = client.post(f"/{SECRET}/token", data={
        "grant_type": "authorization_code", "code": code, "code_verifier": "wrong"})
    assert r.status_code == 400


def test_redirect_outside_claude_rejected():
    _, challenge = pkce()
    assert authorize(challenge, "https://evil.example/cb").status_code == 400


def test_forged_or_access_token_cannot_be_used_as_refresh():
    r = client.post(f"/{SECRET}/token", data={"grant_type": "refresh_token", "refresh_token": "abc.def"})
    assert r.status_code == 400
