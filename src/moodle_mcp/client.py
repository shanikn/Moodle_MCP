#  sends a request to Moodle and returns the JSON
import functools
from typing import Any
import logging
import time

import httpx
from moodle_mcp.config import get_site

# httpx logs every request at INFO; keep the MCP server output quiet
logging.getLogger("httpx").setLevel(logging.WARNING)

# one shared client: reuses the connection and SSL setup instead of rebuilding them per request
_http = httpx.Client(timeout=30)

class MoodleError(Exception):
    """Moodle returned an error (it does this with HTTP 200)."""

def _flatten(params: dict) -> dict:
    """{"courseids: [5, 7]} -> {"courseids[0]: 5, "courseids[1]: 7}"""
    flat = {}
    for key, value in params.items():
        if isinstance(value, list):
            for i, item in enumerate(value):
                flat[f"{key}[{i}]"] = item
        else:
            flat[key] = value
    return flat

def call(wsfunction: str, year: int | None = None, **params) -> Any:  # parsed JSON
    site = get_site(year)
    data = {
        "wstoken": site.token,
        "wsfunction": wsfunction,
        "moodlewsrestformat": "json",
        # apply Moodle text filters, e.g. multilang: "רשתותComputer Networks" -> "Computer Networks"
        "moodlewssettingfilter": "true",
        **_flatten(params),
    }
    url = f"{site.url}/webservice/rest/server.php"
    response = _http.post(url, data=data)
    if response.status_code >= 500:
        # the university server sometimes answers 502 under load; one retry usually works
        time.sleep(1)
        response = _http.post(url, data=data)
    response.raise_for_status()
    result = response.json()
    if isinstance(result, dict) and "exception" in result:
        raise MoodleError(f"{result['errorcode']}: {result['message']}")
    return result

@functools.cache
def get_user_id(year: int | None = None) -> int:
    return call("core_webservice_get_site_info", year=year)["userid"]
