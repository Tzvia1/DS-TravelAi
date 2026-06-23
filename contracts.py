"""FROZEN CONTRACT v1 — do not change without a team vote."""
from dataclasses import dataclass

# The interest buttons in the UI map exactly to these category keys.
INTERESTS = ["architecture", "art", "music", "history",
             "food", "cafe", "museum", "nature"]


@dataclass
class Place:
    name: str          # "Bauhaus Center"
    category: str      # one of INTERESTS
    lat: float
    lon: float
    blurb: str = ""    # short factual note from the data source; may be empty

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
