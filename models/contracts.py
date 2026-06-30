"""FROZEN CONTRACT v1 — do not change without a team vote."""
from dataclasses import dataclass

# The interest buttons in the UI map exactly to these category keys.
INTERESTS = ["architecture", "art", "music", "history",
             "food", "cafe", "museum", "nature",
             "beach", "bar", "theater", "viewpoint",
             "market", "cinema", "religion", "kids"]


@dataclass
class Place:
    name: str          # "Bauhaus Center"
    category: str      # one of INTERESTS
    lat: float
    lon: float
    blurb: str = ""    # short factual note from the data source; may be empty


# ---- Shared helper (additive; no shape change to the frozen contract) ----
# Maps a target walking duration to a stop count so the UI's duration slider
# and the agent agree on the same number. Floor of 4 stops (a tour shorter than
# that feels thin), +1 per extra ~30 min beyond an hour, capped at 6.
#   <=60 min -> 4 stops, ~90 -> 5, >=120 -> 6
def minutes_to_stops(minutes: int) -> int:
    return max(4, min(6, 4 + (int(minutes) - 60) // 30))

# ---- Tool signatures (Tzvia implements these in tools.py) -------------
# get_nearby_places(location: str, interests: list[str],
#                   radius_m: int = 800, limit: int = 12) -> list[Place]
#
# order_walking_route(places: list[Place],
#                     start_lat: float | None = None,
#                     start_lon: float | None = None) -> list[Place]
# ----------------------------------------------------------------------

# ---- Final answer the agent returns to the UI ------------------------
# {
#   "intro": "A short friendly sentence about the walk.",
#   "stops": [
#     {"name": str, "category": str, "lat": float, "lon": float,
#      "narration": "one friendly sentence about this stop"}
#   ]
# }
# ----------------------------------------------------------------------
