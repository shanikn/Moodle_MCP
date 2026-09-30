# the logic for Moodle's site-wide search
from moodle_mcp.client import call
from moodle_mcp.formatting import fmt_date, html_to_text

SNIPPET = 300


def search(query: str, page: int = 0, year: int | None = None) -> dict:
    result = call("core_search_get_results", year=year, query=query, page=page)
    return {
        "total": result.get("totalcount", 0),
        "page": page,
        "results": [{
            "title": html_to_text(r["title"]),
            "kind": f"{r.get('componentname')}/{r.get('areaname')}",  # e.g. mod_forum/post, mod_resource/activity
            "course": html_to_text(r.get("coursefullname", "")),
            "snippet": html_to_text(r.get("content", ""))[:SNIPPET],
            "modified": fmt_date(r.get("timemodified", 0)),
            "url": r.get("docurl"),
        } for r in result.get("results", [])],
    }
