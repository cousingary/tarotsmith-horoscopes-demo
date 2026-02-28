"""
chart_parser.py
---------------
Reads weekly_ephemeris.csv and parses planetary position strings
into structured dicts for downstream processing.

CSV column format:  Sign DDD°MM'  e.g.  "Pisces 3°52'"
Retrograde flag: "Rx" suffix  e.g.  "Pisces 21°10' Rx"
Birth data columns are present in the schema but ignored at generation time.
"""

import csv
import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

SIGN_DEGREES = {sign: i * 30 for i, sign in enumerate(SIGNS)}

TRANSIT_PLANETS = [
    "Sun", "Moon", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
    "Node", "Lilith", "Chiron",
]


def parse_position(raw: str) -> dict | None:
    """
    Parse "Pisces 3°52'" or "Pisces 3°52' Rx" into a structured dict.

    Returns:
        {
            "sign": str,
            "degrees": float,       # degrees within sign (0-29.99)
            "abs_deg": float,       # absolute ecliptic degree (0-359.99)
            "retrograde": bool,
        }
    or None if the string is empty or unparseable.
    """
    if not raw or not raw.strip():
        return None

    raw = raw.strip()
    retrograde = "Rx" in raw
    raw = raw.replace("Rx", "").strip()

    pattern = r"^(\w+)\s+(\d+).(\d+).$"
    match = re.match(pattern, raw)
    if not match:
        logger.debug("Could not parse position string: %r", raw)
        return None

    sign, deg_str, min_str = match.groups()
    if sign not in SIGN_DEGREES:
        logger.debug("Unknown sign: %r", sign)
        return None

    degrees = int(deg_str) + int(min_str) / 60
    abs_deg = SIGN_DEGREES[sign] + degrees

    return {
        "sign": sign,
        "degrees": round(degrees, 4),
        "abs_deg": round(abs_deg, 4),
        "retrograde": retrograde,
    }


def load_weeks(csv_path: str | Path) -> list[dict]:
    """
    Load all rows from the ephemeris CSV and return a list of week dicts.
    Each dict contains parsed transit positions and raw week metadata.
    """
    path = Path(csv_path)
    weeks = []

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            week = {
                "week_start": row.get("week_start", "").strip(),
                "week_end": row.get("week_end", "").strip(),
                "transits": {},
            }

            for planet in TRANSIT_PLANETS:
                col = f"{planet}_transit"
                raw = row.get(col, "")
                parsed = parse_position(raw)
                if parsed:
                    week["transits"][planet] = parsed
                else:
                    logger.debug(
                        "Week %s: no transit position for %s",
                        week["week_start"], planet,
                    )

            if week["week_start"] and week["transits"]:
                weeks.append(week)

    logger.info("Loaded %d weeks from %s", len(weeks), path)
    return weeks
