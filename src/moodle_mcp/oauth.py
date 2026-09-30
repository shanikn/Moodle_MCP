"""Minimal OAuth 2.1 endpoints so claude.ai can add this server as a custom connector.

claude.ai always runs an OAuth sign-in when adding a remote connector. This server is
private because its URL contains an unguessable secret path, so the sign-in here approves
automatically: it exists only to give claude.ai the flow it expects. Every OAuth address
contains the secret too (root /.well-known/... stays 404), so nothing reveals the path.

Nothing is kept in memory: authorization codes and tokens are signed (HMAC) with a key
derived from the secret, so any Cloud Run instance can verify them after a restart.
"""
import base64
import hashlib
import hmac
import json
import secrets
import time
from urllib.parse import urlencode, urlsplit

from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response

# Only claude.ai may receive codes, so a leaked URL can't be used to phish a token elsewhere.
ALLOWED_REDIRECT_HOSTS = {"claude.ai", "claude.com"}
CODE_TTL = 300  # seconds


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


class OAuth:
    def __init__(self, secret: str):
        self.secret = secret
        self.prefix = f"/{secret}"
        self.key = hashlib.sha256(f"moodle-mcp-oauth:{secret}".encode()).digest()

    # --- signing helpers ---------------------------------------------------------------
    def _sign(self, payload: dict) -> str:
        body = _b64(json.dumps(payload, separators=(",", ":")).encode())
        mac = _b64(hmac.new(self.key, body.encode(), hashlib.sha256).digest())
        return f"{body}.{mac}"

    def _verify(self, token: str, kind: str) -> dict | None:
        try:
            body, mac = token.split(".")
            expected = _b64(hmac.new(self.key, body.encode(), hashlib.sha256).digest())
            if not hmac.compare_digest(mac, expected):
                return None
            payload = json.loads(_unb64(body))
        except Exception:
            return None
        if payload.get("kind") != kind or payload.get("exp", float("inf")) < time.time():
            return None
        return payload

    # --- routing -----------------------------------------------------------------------
    def handles(self, path: str) -> bool:
        return path in {
            f"/.well-known/oauth-protected-resource{self.prefix}/mcp",
            f"/.well-known/oauth-authorization-server{self.prefix}",
            f"/.well-known/openid-configuration{self.prefix}",
            f"{self.prefix}/.well-known/oauth-authorization-server",
            f"{self.prefix}/.well-known/openid-configuration",
            f"{self.prefix}/register",
            f"{self.prefix}/authorize",
            f"{self.prefix}/token",
        }

    async def __call__(self, scope, receive, send):
        request = Request(scope, receive)
        path = scope["path"]
        if path.startswith("/.well-known/oauth-protected-resource"):
            response = self.protected_resource(request)
        elif path.endswith("/register"):
            response = await self.register(request)
        elif path.endswith("/authorize"):
            response = self.authorize(request)
        elif path.endswith("/token"):
            response = await self.token(request)
        else:
            response = self.server_metadata(request)
        await response(scope, receive, send)

    def _base(self, request: Request) -> str:
        # Cloud Run terminates HTTPS in front of the app; the original scheme is in this header.
        proto = request.headers.get("x-forwarded-proto", request.url.scheme)
        return f"{proto}://{request.headers['host']}"

    # --- endpoints ---------------------------------------------------------------------
    def protected_resource(self, request: Request) -> Response:
        base = self._base(request)
        return JSONResponse({
            "resource": f"{base}{self.prefix}/mcp",
            "authorization_servers": [f"{base}{self.prefix}"],
        })

    def server_metadata(self, request: Request) -> Response:
        issuer = f"{self._base(request)}{self.prefix}"
        return JSONResponse({
            "issuer": issuer,
            "authorization_endpoint": f"{issuer}/authorize",
            "token_endpoint": f"{issuer}/token",
            "registration_endpoint": f"{issuer}/register",
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "code_challenge_methods_supported": ["S256"],
            "token_endpoint_auth_methods_supported": ["none", "client_secret_post", "client_secret_basic"],
        })

    async def register(self, request: Request) -> Response:
        # Dynamic client registration: any client gets an id; nothing is stored.
        try:
            info = await request.json()
        except Exception:
            info = {}
        return JSONResponse({
            "client_id": "claude-" + secrets.token_urlsafe(12),
            "client_id_issued_at": int(time.time()),
            "redirect_uris": info.get("redirect_uris", []),
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "none",
        }, status_code=201)

    def authorize(self, request: Request) -> Response:
        q = request.query_params
        redirect_uri = q.get("redirect_uri", "")
        parts = urlsplit(redirect_uri)
        if parts.scheme != "https" or parts.hostname not in ALLOWED_REDIRECT_HOSTS:
            return JSONResponse({"error": "invalid_request", "error_description": "redirect_uri not allowed"}, 400)
        if q.get("response_type") != "code" or q.get("code_challenge_method") != "S256" or not q.get("code_challenge"):
            return JSONResponse({"error": "invalid_request", "error_description": "code + S256 PKCE required"}, 400)
        code = self._sign({"kind": "code", "cc": q["code_challenge"], "ru": redirect_uri,
                           "exp": time.time() + CODE_TTL})
        params = {"code": code}
        if "state" in q:
            params["state"] = q["state"]
        sep = "&" if parts.query else "?"
        return RedirectResponse(f"{redirect_uri}{sep}{urlencode(params)}", status_code=302)

    async def token(self, request: Request) -> Response:
        form = await request.form()
        grant = form.get("grant_type")
        if grant == "authorization_code":
            code = self._verify(form.get("code", ""), "code")
            verifier = form.get("code_verifier", "")
            if not code or not verifier:
                return JSONResponse({"error": "invalid_grant"}, 400)
            if _b64(hashlib.sha256(verifier.encode()).digest()) != code["cc"]:
                return JSONResponse({"error": "invalid_grant", "error_description": "PKCE check failed"}, 400)
            if form.get("redirect_uri") and form["redirect_uri"] != code["ru"]:
                return JSONResponse({"error": "invalid_grant", "error_description": "redirect_uri mismatch"}, 400)
        elif grant == "refresh_token":
            if not self._verify(form.get("refresh_token", ""), "refresh"):
                return JSONResponse({"error": "invalid_grant"}, 400)
        else:
            return JSONResponse({"error": "unsupported_grant_type"}, 400)
        return JSONResponse({
            "access_token": self._sign({"kind": "access", "n": secrets.token_urlsafe(8)}),
            "token_type": "Bearer",
            "expires_in": 30 * 24 * 3600,
            "refresh_token": self._sign({"kind": "refresh", "n": secrets.token_urlsafe(8)}),
        }, headers={"Cache-Control": "no-store"})
