import re
from pathlib import Path

import pytest

from moodle_mcp import runi
from moodle_mcp.redact import dprint, mask

FAKE_ID = "000000018"  # passes the Israeli id checksum, like a real one
FAKE_TOKEN = "0123abcd-ef01-2345-6789-abcdef012345-01234567-89ab"  # shape of Yedion's page Token
FAKE_SAML = "PHNhbWxwOlJlc3BvbnNlIHhtbG5zOnNhbWxwPSJ1cm46b2FzaXM6bmFtZXM6dGM6U0FNTDoyLjA="
FAKE_COOKIE = "a3f1c9e07b2d4e8f9a6b5c4d3e2f1a0b"


@pytest.mark.parametrize("secret", [
    FAKE_ID, f"-N{FAKE_ID}", f"-N{FAKE_TOKEN}", FAKE_TOKEN, FAKE_SAML, FAKE_COOKIE, "0541234567",
    f"ExamBank -N{FAKE_ID},-N{FAKE_TOKEN},-N20,-A,R1C1",
])
def test_mask_hides_ids_and_tokens(secret):
    masked = mask(f"before {secret} after")
    for part in (FAKE_ID, FAKE_TOKEN, FAKE_SAML, FAKE_COOKIE, "0541234567"):
        assert part not in masked
    assert masked.startswith("before ") and masked.endswith(" after")


def test_mask_keeps_what_debugging_needs():
    text = 'course 592, 30/01/2026 09:45, year 2027, HADPASAT_TOCHNIT_BEHINOT, StudentQueryExecution, my.runi.ac.il/my.policy'
    assert mask(text) == text


def test_mask_hides_extra_strings_such_as_the_name():
    assert mask("לוח בחינות ישראלי ישראל", extra=("ישראלי", "ישראל")) == "לוח בחינות <hidden> <hidden>"


def test_dprint_masks_everything_it_prints(capsys):
    dprint("hidden:", {"TZ": FAKE_ID, "Token": FAKE_TOKEN}, f"args=-N{FAKE_ID},-N{FAKE_TOKEN}")
    out = capsys.readouterr().out
    assert FAKE_ID not in out and FAKE_TOKEN not in out
    assert "hidden:" in out


def test_runi_error_messages_are_masked():
    exc = runi.RuniError(f"page for {FAKE_ID} with Token {FAKE_TOKEN} and cookie {FAKE_COOKIE}")
    assert FAKE_ID not in str(exc) and FAKE_TOKEN not in str(exc) and FAKE_COOKIE not in str(exc)


def _is_israeli_id(number: str) -> bool:
    total = 0
    for i, digit in enumerate(number):
        n = int(digit) * (1 + i % 2)
        total += n // 10 + n % 10
    return total % 10 == 0


def test_no_real_looking_id_number_in_the_repo():
    """A 9-digit number with a valid id checksum in a tracked text file is most likely a real
    student's id copied from a Yedion page. Only the fake one is allowed."""
    root = Path(__file__).parent.parent
    found = []
    for path in [*root.glob("*.md"), *root.glob("src/**/*.py"), *root.glob("tests/**/*.py"),
                 *root.glob("tests/fixtures/*"), *root.glob("docs/**/*")]:
        if not path.is_file():
            continue
        for number in re.findall(r"(?<!\d)\d{9}(?!\d)", path.read_text(encoding="utf-8", errors="ignore")):
            if number != FAKE_ID and _is_israeli_id(number):
                found.append(f"{path.relative_to(root)}: {mask(number)}")  # never print the number itself
    assert not found, found
