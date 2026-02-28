"""
pipeline.py
-----------
Orchestrates the full weekly generation cycle.

Sequence:
  1. Load weeks from CSV via chart_parser
  2. Derive aspects, dignity, lunar phase, decan via transit_engine
  3. Build 24 structured briefs (12 Sun, 12 Rising)
  4. Send briefs to writer in batches of 4
  5. Run editor pass on each completed batch
  6. Retry flagged signs once if editor returns "revise"
  7. Assemble and return the week's full output dict

The writer and editor are called via the LLM client module (not included
in this mirror). Model selection, temperature, and max_tokens are
controlled by environment variables.

Usage:
    from pipeline import run_week
    result = run_week("2026-03-02")
    # result = {week_start, week_end, sun: {sign: text}, rising: {sign: text}, editor_reports: {...}}
"""

import logging
from src.chart_parser import load_weeks
from src.transit_engine import (
    find_aspects, solar_dignity, lunar_phase,
    sign_relationship, whole_sign_houses, decan_card,
)

logger = logging.getLogger(__name__)

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

BATCH_SIZE = 4


# ---------------------------------------------------------------------------
# BRIEF BUILDERS
# ---------------------------------------------------------------------------

def build_sun_brief(sign: str, week: dict) -> dict:
    """
    Assemble the structured JSON brief sent to the Sun sign writer
    for a single sign.
    """
    transits = week["transits"]
    sun = transits.get("Sun", {})
    moon = transits.get("Moon", {})

    aspects = find_aspects(transits)
    sign_aspects = [
        a for a in aspects
        if a["planet_a"] == "Sun" or a["planet_b"] == "Sun"
    ]

    planet_digest = {}
    for planet, pos in transits.items():
        if planet == "Sun":
            continue
        planet_digest[planet] = {
            "sign": pos["sign"],
            "degrees": round(pos["degrees"], 1),
            "retrograde": pos["retrograde"],
            "sign_relation_to_sun": sign_relationship(pos["sign"], sign),
        }

    return {
        "product": "Sun",
        "sign": sign,
        "week_start": week["week_start"],
        "week_end": week["week_end"],
        "sun_sign": sun.get("sign"),
        "sun_degrees": round(sun.get("degrees", 0), 1),
        "sun_dignity": solar_dignity(sign),
        "decan_card": decan_card(sun.get("abs_deg", 0)),
        "lunar_phase": lunar_phase(
            sun.get("abs_deg", 0),
            moon.get("abs_deg", 0),
        ),
        "planet_digest": planet_digest,
        "aspects": sign_aspects[:8],  # tightest 8 aspects only
    }


def build_rising_brief(rising_sign: str, week: dict) -> dict:
    """
    Assemble the structured JSON brief sent to the Rising sign writer
    for a single ascendant.
    """
    transits = week["transits"]
    sun = transits.get("Sun", {})
    moon = transits.get("Moon", {})

    house_placements = whole_sign_houses(rising_sign, transits)
    aspects = find_aspects(transits)

    # Chart ruler(s): primary Hellenistic rulership
    RULERS = {
        "Aries": ["Mars"], "Taurus": ["Venus"], "Gemini": ["Mercury"],
        "Cancer": ["Moon"], "Leo": ["Sun"], "Virgo": ["Mercury"],
        "Libra": ["Venus"], "Scorpio": ["Mars", "Pluto"],
        "Sagittarius": ["Jupiter"], "Capricorn": ["Saturn"],
        "Aquarius": ["Saturn", "Uranus"], "Pisces": ["Jupiter", "Neptune"],
    }

    rulers = RULERS.get(rising_sign, [])
    chart_rulers = {
        r: house_placements.get(r) for r in rulers if r in house_placements
    }

    return {
        "product": "Rising",
        "sign": rising_sign,
        "week_start": week["week_start"],
        "week_end": week["week_end"],
        "house_placements": house_placements,
        "chart_rulers": chart_rulers,
        "lunar_phase": lunar_phase(
            sun.get("abs_deg", 0),
            moon.get("abs_deg", 0),
        ),
        "aspects": aspects[:8],
    }


# ---------------------------------------------------------------------------
# BATCH BUILDER
# ---------------------------------------------------------------------------

def build_all_briefs(week: dict) -> dict:
    """Build all 24 briefs and return them pre-batched."""
    sun_briefs    = [build_sun_brief(sign, week) for sign in SIGNS]
    rising_briefs = [build_rising_brief(sign, week) for sign in SIGNS]

    def batch(lst):
        return [lst[i:i + BATCH_SIZE] for i in range(0, len(lst), BATCH_SIZE)]

    return {
        "week_start":     week["week_start"],
        "week_end":       week["week_end"],
        "sun_batches":    batch(sun_briefs),
        "rising_batches": batch(rising_briefs),
    }


# ---------------------------------------------------------------------------
# PIPELINE ENTRY POINT
# ---------------------------------------------------------------------------

def run_week(target_week_start: str, csv_path: str = "data/weekly_snapshot_example.csv") -> dict:
    """
    Run the full generation pipeline for one week.

    The LLM writer and editor calls are handled by the private
    write module (not included in this mirror). This function
    documents the contract: what goes in, what comes out.

    Input:  week_start date string (YYYY-MM-DD)
    Output: {
        week_start: str,
        week_end:   str,
        sun:        {sign: horoscope_text, ...},    # 12 entries
        rising:     {sign: horoscope_text, ...},    # 12 entries
        editor_reports: {
            sun:    [editor_json_per_batch, ...],   # 3 batches
            rising: [editor_json_per_batch, ...],
        }
    }
    """
    weeks = load_weeks(csv_path)
    week = next((w for w in weeks if w["week_start"] == target_week_start), None)

    if week is None:
        raise ValueError(f"Week {target_week_start} not found in {csv_path}")

    brief_data = build_all_briefs(week)
    logger.info(
        "Built briefs for week %s: %d sun batches, %d rising batches",
        target_week_start,
        len(brief_data["sun_batches"]),
        len(brief_data["rising_batches"]),
    )

    # LLM generation and editor loop handled by private write module.
    # Returns assembled dict in the format described above.
    raise NotImplementedError(
        "Writer and editor modules are not included in this public mirror. "
        "See README for architecture documentation."
    )
