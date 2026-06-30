"""
Pure, UI-free logic for the Walking-Tour app.

Kept separate from app.py so it can be unit-tested without a running Streamlit
context — app.py executes Streamlit calls (st.set_page_config, widgets) at
import time, which a plain `import app` in pytest can't satisfy. Both app.py
and tests/test_app_unit.py import from here.
"""
import json
import re

from models.contracts import minutes_to_stops

# Valid Earth coordinate ranges — a hallucinating model could emit lat=999,
# which would silently break the map, so we range-check before plotting.
_LAT_RANGE = (-90.0, 90.0)
_LON_RANGE = (-180.0, 180.0)


def compose_note(duration_min, extra=""):
    """Fold the chosen duration (and any refine text) into the agent's note.

    The frozen contract's run_agent() has no duration parameter, so duration
    travels to the agent through this free-text note.
    """
    parts = []
    if duration_min:
        parts.append(f"Aim for roughly {duration_min} minutes of walking total.")
    if extra:
        parts.append(extra)
    return "  ".join(parts)


def parse_tour(raw):
    """Turn the agent's output into a dict, tolerating ```json fences / junk.

    The real agent returns a JSON *string* (the model's content). We defend
    against the model occasionally wrapping it in markdown fences or adding
    stray prose, so the UI never crashes on a bad payload. Returns None when
    nothing usable can be parsed.
    """
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        return None

    text = raw.strip()

    # Strip ```json ... ``` or ``` ... ``` fences if present.
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()

    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        # Last resort: grab the first {...} block out of surrounding prose.
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except (json.JSONDecodeError, TypeError):
                return None
        return None


def valid_coord(stop):
    """True only if the stop has real, in-range Earth lat/lon we can map."""
    try:
        lat = float(stop["lat"])
        lon = float(stop["lon"])
    except (KeyError, TypeError, ValueError):
        return False
    return _LAT_RANGE[0] <= lat <= _LAT_RANGE[1] and _LON_RANGE[0] <= lon <= _LON_RANGE[1]


def fake_agent(location, interests, note=""):
    """Offline stand-in for Chavi's agent. Returns the same dict shape.

    Reads a target duration out of the note (e.g. "~90 minutes") so demo mode
    visibly reacts to the duration control.
    """
    sample = [
        {"name": "Bauhaus Center", "category": "architecture",
         "lat": 32.0773, "lon": 34.7745,
         "narration": "Heart of the White City design scene."},
        {"name": "Levontin 7", "category": "music",
         "lat": 32.0648, "lon": 34.7766,
         "narration": "A beloved spot for intimate live music."},
        {"name": "Cafe Xoho", "category": "cafe",
         "lat": 32.0760, "lon": 34.7730,
         "narration": "Pause here for excellent coffee and a bite."},
        {"name": "Rubin Museum", "category": "museum",
         "lat": 32.0686, "lon": 34.7710,
         "narration": "A quiet house-museum of early Israeli art."},
        {"name": "Carmel Market", "category": "food",
         "lat": 32.0686, "lon": 34.7685,
         "narration": "Loud, fragrant, and full of things to taste."},
        {"name": "Gan Meir Park", "category": "nature",
         "lat": 32.0742, "lon": 34.7745,
         "narration": "A leafy break in the middle of the city."},
        {"name": "Independence Hall", "category": "history",
         "lat": 32.0641, "lon": 34.7702,
         "narration": "Where the state was declared in 1948."},
    ]
    chosen = [s for s in sample if s["category"] in interests] or sample[:4]

    # Pull a duration out of the note and size the walk to it.
    m = re.search(r"(\d+)\s*min", note or "")
    if m:
        chosen = chosen[:minutes_to_stops(int(m.group(1)))]

    intro = (f"A short walk from {location or 'your starting point'} "
             f"for {', '.join(interests) or 'curious'} lovers.")
    if note:
        intro += f"  (adjusted for: {note})"
    return {"intro": intro, "stops": chosen}
