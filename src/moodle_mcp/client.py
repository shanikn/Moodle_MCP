#  sends a request to Moodle and returns the JSON
import functools
import httpx
from moodle_mcp.config import get_site

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

def call(wsfunction: str, year: int | None = None, **params) -> dict | list:
    site = get_site(year)
    data = {
        "wstoken": site.token,
        "wsfunction": wsfunction,
        "moodlewsrestformat": "json",
        **_flatten(params),
    }
    response = httpx.post(f"{site.url}/webservice/rest/server.php", data=data, timeout=30)
    response.raise_for_status()
    result = response.json()
    if isinstance(result, dict) and "exception" in result:
        raise MoodleError(f"{result['errorcode']}: {result['message']}")
    return result

@functools.cache
def get_user_id(year: int | None = None) -> int:
    return call("core_webservice_get_site_info", year=year)["userid"]
