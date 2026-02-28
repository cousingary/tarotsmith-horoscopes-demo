"""
transit_engine.py
-----------------
Derives astrological relationships from parsed planetary positions.

Computes:
  - Aspects between transit planets (ranked by orb, filtered by significance)
  - Solar dignity for each of the 12 Sun signs
  - Lunar phase from Sun-Moon separation
  - Sign relationship of each planet to the Sun's sign
  - Whole-sign house placements for all 12 Rising sign variants
  - Retrograde flags
  - Decan card (Golden Dawn/Thoth system) from Sun's exact degree

Aspect orbs, dignity tables, decan assignments, and sign relationship
logic are defined here. The writing engine reads the output of this
module — it does not do its own chart arithmetic.
"""

from math import fabs

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# ---------------------------------------------------------------------------
# ASPECT DEFINITIONS
# ---------------------------------------------------------------------------

ASPECTS = {
    "conjunction":  0,
    "sextile":     60,
    "square":      90,
    "trine":      120,
    "quincunx":   150,
    "opposition": 180,
}

ASPECT_ORBS = {
    "conjunction":  8,
    "sextile":      5,
    "square":       7,
    "trine":        7,
    "quincunx":     3,
    "opposition":   8,
}

# ---------------------------------------------------------------------------
# DIGNITY TABLE
# ---------------------------------------------------------------------------

DIGNITY = {
    # planet: {domicile: [...], exaltation: str, detriment: [...], fall: str}
    "Sun":     {"domicile": ["Leo"],         "exaltation": "Aries",       "detriment": ["Aquarius"],          "fall": "Libra"},
    "Moon":    {"domicile": ["Cancer"],      "exaltation": "Taurus",      "detriment": ["Capricorn"],         "fall": "Scorpio"},
    "Mercury": {"domicile": ["Gemini", "Virgo"], "exaltation": "Virgo",   "detriment": ["Sagittarius", "Pisces"], "fall": "Pisces"},
    "Venus":   {"domicile": ["Taurus", "Libra"], "exaltation": "Pisces",  "detriment": ["Aries", "Scorpio"],  "fall": "Virgo"},
    "Mars":    {"domicile": ["Aries", "Scorpio"], "exaltation": "Capricorn", "detriment": ["Libra", "Taurus"], "fall": "Cancer"},
    "Jupiter": {"domicile": ["Sagittarius", "Pisces"], "exaltation": "Cancer", "detriment": ["Gemini", "Virgo"], "fall": "Capricorn"},
    "Saturn":  {"domicile": ["Capricorn", "Aquarius"], "exaltation": "Libra", "detriment": ["Cancer", "Leo"],  "fall": "Aries"},
}


def solar_dignity(sun_sign: str) -> str:
    """Return the Sun's essential dignity in the given sign."""
    d = DIGNITY["Sun"]
    if sun_sign in d["domicile"]:
        return "domicile"
    if sun_sign == d["exaltation"]:
        return "exaltation"
    if sun_sign in d["detriment"]:
        return "detriment"
    if sun_sign == d["fall"]:
        return "fall"
    return "peregrine"


# ---------------------------------------------------------------------------
# ASPECT ENGINE
# ---------------------------------------------------------------------------

def angular_distance(a: float, b: float) -> float:
    """Shortest arc between two ecliptic degrees."""
    diff = fabs(a - b) % 360
    return diff if diff <= 180 else 360 - diff


def find_aspects(transits: dict) -> list[dict]:
    """
    Return all significant aspects between transit planets, ranked by orb.
    Filters out minor planet pairs (e.g. Lilith-Chiron) unless involving
    a personal or social planet.
    """
    planets = list(transits.keys())
    aspects = []

    PERSONAL = {"Sun", "Moon", "Mercury", "Venus", "Mars"}
    SOCIAL    = {"Jupiter", "Saturn"}

    for i in range(len(planets)):
        for j in range(i + 1, len(planets)):
            p1, p2 = planets[i], planets[j]
            if p1 not in PERSONAL | SOCIAL and p2 not in PERSONAL | SOCIAL:
                continue

            pos1 = transits[p1]["abs_deg"]
            pos2 = transits[p2]["abs_deg"]
            dist = angular_distance(pos1, pos2)

            for aspect_name, angle in ASPECTS.items():
                orb = fabs(dist - angle)
                if orb <= ASPECT_ORBS[aspect_name]:
                    aspects.append({
                        "planet_a": p1,
                        "planet_b": p2,
                        "aspect": aspect_name,
                        "orb": round(orb, 2),
                    })

    return sorted(aspects, key=lambda x: x["orb"])


# ---------------------------------------------------------------------------
# LUNAR PHASE
# ---------------------------------------------------------------------------

PHASE_NAMES = [
    (0,   45,  "New Moon"),
    (45,  90,  "Waxing Crescent"),
    (90,  135, "First Quarter"),
    (135, 180, "Waxing Gibbous"),
    (180, 225, "Full Moon"),
    (225, 270, "Waning Gibbous"),
    (270, 315, "Last Quarter"),
    (315, 360, "Waning Crescent"),
]


def lunar_phase(sun_abs: float, moon_abs: float) -> dict:
    """Derive lunar phase name and Sun-Moon separation."""
    separation = (moon_abs - sun_abs) % 360
    phase = next(
        name for lo, hi, name in PHASE_NAMES
        if lo <= separation < hi
    )
    return {
        "phase": phase,
        "separation_deg": round(separation, 1),
    }


# ---------------------------------------------------------------------------
# SIGN RELATIONSHIP
# ---------------------------------------------------------------------------

def sign_relationship(planet_sign: str, sun_sign: str) -> str:
    """
    Return the whole-sign relationship between a planet's sign and the Sun's sign.
    Used by the writing engine to apply the solar framework.
    """
    sun_idx = SIGNS.index(sun_sign)
    planet_idx = SIGNS.index(planet_sign)
    diff = (planet_idx - sun_idx) % 12

    relationships = {
        0: "conjunct",
        1: "semisextile",
        2: "sextile",
        3: "square",
        4: "trine",
        5: "quincunx",
        6: "opposition",
        7: "quincunx",
        8: "trine",
        9: "square",
        10: "sextile",
        11: "semisextile",
    }
    return relationships[diff]


# ---------------------------------------------------------------------------
# WHOLE-SIGN HOUSE PLACEMENTS
# ---------------------------------------------------------------------------

def whole_sign_houses(rising_sign: str, transits: dict) -> dict:
    """
    Return house number (1-12) for each transit planet given a Rising sign,
    using whole-sign house system.
    """
    asc_idx = SIGNS.index(rising_sign)
    placements = {}

    for planet, pos in transits.items():
        planet_idx = SIGNS.index(pos["sign"])
        house = ((planet_idx - asc_idx) % 12) + 1
        placements[planet] = {
            "house": house,
            "sign": pos["sign"],
            "degrees": pos["degrees"],
            "retrograde": pos["retrograde"],
        }

    return placements


# ---------------------------------------------------------------------------
# DECAN CARD (Golden Dawn / Thoth system)
# ---------------------------------------------------------------------------

# 36 decans in order: each sign has 3 x 10-degree decans.
# Card assignments follow the Golden Dawn system.
DECAN_CARDS = [
    # Aries
    "Two of Wands", "Three of Wands", "Four of Wands",
    # Taurus
    "Five of Pentacles", "Six of Pentacles", "Seven of Pentacles",
    # Gemini
    "Eight of Swords", "Nine of Swords", "Ten of Swords",
    # Cancer
    "Two of Cups", "Three of Cups", "Four of Cups",
    # Leo
    "Five of Wands", "Six of Wands", "Seven of Wands",
    # Virgo
    "Eight of Pentacles", "Nine of Pentacles", "Ten of Pentacles",
    # Libra
    "Two of Swords", "Three of Swords", "Four of Swords",
    # Scorpio
    "Five of Cups", "Six of Cups", "Seven of Cups",
    # Sagittarius
    "Eight of Wands", "Nine of Wands", "Ten of Wands",
    # Capricorn
    "Two of Pentacles", "Three of Pentacles", "Four of Pentacles",
    # Aquarius
    "Five of Swords", "Six of Swords", "Seven of Swords",
    # Pisces
    "Eight of Cups", "Nine of Cups", "Ten of Cups",
]


def decan_card(sun_abs_deg: float) -> str:
    """Return the Minor Arcana card for the Sun's current decan."""
    decan_index = int(sun_abs_deg // 10) % 36
    return DECAN_CARDS[decan_index]
