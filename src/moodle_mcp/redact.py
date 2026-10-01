# masks personal data and secrets in anything shown to a person or to Claude: error messages and
# debug output. Yedion pages and form arguments carry the student's id number and session tokens
# (e.g. ExamBank arguments "-N<id>,-N<token>,..."); never print page content without mask().
import re
import sys

_PATTERNS = [
    # uuid-like tokens, e.g. Yedion's page Token "0123abcd-ef01-2345-6789-abcdef012345-01234567-89ab"
    (re.compile(r"\b[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{3,}){2,}\b"), "<token>"),
    # long opaque strings: hex / base64 / url-safe tokens (cookies, SAMLResponse, TOKEN= params)
    (re.compile(r"(?<![\w/.-])[A-Za-z0-9+/_-]{28,}={0,2}"), "<token>"),
    # 5+ digit numbers: id numbers (also inside "-N000000018"), phone numbers, examinee numbers
    (re.compile(r"\d{5,}"), "<n>"),
]


def mask(text: object, extra: tuple[str, ...] = ()) -> str:
    """str(text) with 5+ digit numbers and token-like strings replaced. `extra` lists other
    strings to hide (e.g. the student's name, which no pattern can recognise)."""
    text = str(text)
    for secret in extra:
        if secret:
            text = text.replace(secret, "<hidden>")
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def dprint(*parts: object, extra: tuple[str, ...] = (), file=None) -> None:
    """print() for debugging and discovery scripts: everything goes through mask()."""
    print(*(mask(p, extra) for p in parts), file=file or sys.stdout)
