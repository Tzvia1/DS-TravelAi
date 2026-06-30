"""Tzvia's tools: get_nearby_places, order_walking_route, validate_request.

Data source: OpenStreetMap — Nominatim (geocoding) + Overpass (nearby places).
Both are free, keyless community servers; we send a descriptive User-Agent
and keep queries minimal per their usage etiquette.
"""
from functools import lru_cache
from math import radians, sin, cos, asin, sqrt

import requests

from models.contracts import Place, INTERESTS

HEADERS = {"User-Agent": "walking-tour-agent/0.1 (student project)"}
NOMINATIM = "https://nominatim.openstreetmap.org/search"
# Overpass is the slow part. We try a commonly-faster mirror first and fall
# back to the main server, so a slow/overloaded endpoint doesn't stall a build.
# Reorder this list if a mirror misbehaves.
OVERPASS_ENDPOINTS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]

# Each interest -> a list of OSM (key, value) filters to search for.
CATEGORY_OSM = {
    "architecture": [("tourism", "attraction"), ("building", "yes")],
    "art":          [("tourism", "gallery"), ("amenity", "arts_centre")],
    "music":        [("amenity", "music_venue"), ("amenity", "nightclub")],
    "history":      [("historic", "*")],            # "*" = any value
    "food":         [("amenity", "restaurant")],
    "cafe":         [("amenity", "cafe")],
    "museum":       [("tourism", "museum")],
    "nature":       [("leisure", "park"), ("leisure", "garden")],
}


@lru_cache(maxsize=256)
def geocode(address):
    """Address -> (lat, lon). Raises ValueError if not found.

    Cached: the same address geocodes instantly on repeat builds / refines.
    """
    r = requests.get(NOMINATIM,
                      params={"q": address, "format": "json", "limit": 1},
                      headers=HEADERS, timeout=10)
    r.raise_for_status()
    hits = r.json()
    if not hits:
        raise ValueError(f"Could not locate address: {address!r}")
    print(f"-> Geocoded {address!r} to {hits[0]['lat']},{hits[0]['lon']}")
    return float(hits[0]["lat"]), float(hits[0]["lon"])


def _build_overpass_query(lat, lon, interests, radius_m):
    """Build one Overpass query covering all chosen interests."""
    clauses = []
    for interest in interests:
        for key, value in CATEGORY_OSM.get(interest, []):
            sel = f'["{key}"]' if value == "*" else f'["{key}"="{value}"]'
            # node/way/relation around the point, must have a name
            clauses.append(f'nwr(around:{radius_m},{lat},{lon}){sel}["name"];')
    body = "\n".join(clauses)
    return f"[out:json][timeout:25];\n({body}\n);\nout center 50;"


def _which_interest(tags, interests):
    """Decide which chosen interest a result belongs to."""
    for interest in interests:
        for key, value in CATEGORY_OSM.get(interest, []):
            if key in tags and (value == "*" or tags[key] == value):
                return interest
    return interests[0] if interests else "history"


def _query_overpass(query):
    """POST the query to the first Overpass endpoint that answers."""
    last_err = None
    for url in OVERPASS_ENDPOINTS:
        try:
            r = requests.post(url, data={"data": query}, headers=HEADERS, timeout=25)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            last_err = e  # endpoint slow/down — try the next one
    raise last_err


def get_nearby_places(location, interests, radius_m=800, limit=12):
    lat, lon = geocode(location)
    query = _build_overpass_query(lat, lon, interests, radius_m)
    data = _query_overpass(query)

    places = []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name:
            continue
        # ways/relations return center coords; nodes return lat/lon directly
        plat = el.get("lat") or el.get("center", {}).get("lat")
        plon = el.get("lon") or el.get("center", {}).get("lon")
        if plat is None or plon is None:
            continue
        category = _which_interest(tags, interests)
        places.append(Place(name=name, category=category,
                             lat=float(plat), lon=float(plon),
                             blurb=tags.get("description", "")))

    # de-duplicate by name, keep the first of each
    seen, unique = set(), []
    for p in places:
        if p.name not in seen:
            seen.add(p.name)
            unique.append(p)
    return unique[:limit]


def _haversine(a_lat, a_lon, b_lat, b_lon):
    """Distance in metres between two lat/lon points."""
    R = 6371000
    dlat, dlon = radians(b_lat - a_lat), radians(b_lon - a_lon)
    h = sin(dlat / 2) ** 2 + cos(radians(a_lat)) * cos(radians(b_lat)) * sin(dlon / 2) ** 2
    return 2 * R * asin(sqrt(h))


def order_walking_route(places, start_lat=None, start_lon=None):
    remaining = list(places)
    if not remaining:
        return []
    # pick a starting point
    if start_lat is None or start_lon is None:
        current = remaining.pop(0)
        ordered = [current]
        cur_lat, cur_lon = current.lat, current.lon
    else:
        ordered = []
        cur_lat, cur_lon = start_lat, start_lon
    # repeatedly grab the nearest unvisited stop
    while remaining:
        nxt = min(remaining, key=lambda p: _haversine(cur_lat, cur_lon, p.lat, p.lon))
        remaining.remove(nxt)
        ordered.append(nxt)
        cur_lat, cur_lon = nxt.lat, nxt.lon
    return ordered


def validate_request(location, interests):
    """Return (ok: bool, message: str). Call BEFORE running the agent."""
    if not location or not location.strip():
        return False, "Please type a starting address."
    if not interests:
        return False, "Pick at least one interest to build a tour."
    bad = [i for i in interests if i not in INTERESTS]
    if bad:
        return False, f"Unknown interest(s): {bad}. Choose from the buttons."
    return True, ""
