# reads .env and finds the token for each year
import os
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()

MOODLE_BASE_URL = os.environ["MOODLE_BASE_URL"]
TOKENS = {}
for key, value in os.environ.items():
    if key.startswith("MOODLE_TOKEN_"):
        year = int(key.removeprefix("MOODLE_TOKEN_"))
        TOKENS[year] = value
MOODLE_DEFAULT_YEAR = int(os.environ["MOODLE_DEFAULT_YEAR"])


@dataclass
class Site:
    url: str
    token: str


def get_site(year: int | None = None)->Site:
    if year is None:
        year = MOODLE_DEFAULT_YEAR
    if year not in TOKENS:
        raise ValueError(f"No token for {year}. Add MOODLE_TOKEN_{year} to .env")
    return Site(url=f"{MOODLE_BASE_URL}/{year}", token=TOKENS[year])
