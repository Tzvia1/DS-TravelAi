# Tzvia's Guide — Tools & Data 🛠️

**Your area:** the two tools (`get_nearby_places`, `order_walking_route`), the places-API setup, and input validation.
**Your tools are what turn the user's interest buttons into real places on a real map.** If your data is good, the whole demo feels magic; if it's flaky, everything downstream suffers — so you build and test the data layer first.

You know Python basics. You'll mostly use `requests` (HTTP calls) and a little math. No prior maps/GIS experience needed.

---

## Your tasks & dates (from the tracker)

| When | Task | Done when… |
|---|---|---|
| Mon–Tue Jun 22–23 | Get **geocoding** working; confirm the API returns good results | A real address → sensible lat/lon + nearby spots |
| Tue–Thu Jun 23–25 | Build **`get_nearby_places`** | Address + interests → list of real `Place`s |
| Wed–Thu Jun 24–25 | Build **`order_walking_route`** (nearest-next) | A list comes back in walkable order |
| Thu Jun 25 | **Test** both tools on 3 scenarios | Output looks right on 3 address+interest combos |
| Fri Jun 26 (day) | Integration (all-hands) | Real tools wired into the agent + UI |
| Tue–Wed Jun 30–Jul 1 | **Input validation** | Empty address / no interests is caught early |

---

## The frozen contract (Chavi owns it — you build to it)

Everything you write must match `contracts.py`. Don't change these shapes without a team vote — Chavi calls them and Efrat renders them.

```python
# contracts.py
INTERESTS = ["architecture", "art", "music", "history",
             "food", "cafe", "museum", "nature"]

@dataclass
class Place:
    name: str; category: str; lat: float; lon: float; blurb: str = ""

# YOU implement, exactly these signatures:
# get_nearby_places(location: str, interests: list[str],
#                   radius_m: int = 800, limit: int = 12) -> list[Place]
# order_walking_route(places: list[Place],
#                     start_lat: float | None = None,
#                     start_lon: float | None = None) -> list[Place]
```

---

## Step 1 — The places API: OpenStreetMap (free, no key) (Jun 22–23)

Chavi will confirm the team's choice, but the recommended default is **OpenStreetMap**, because it's free and needs **no API key** — perfect for a class project. Two free, keyless services:

- **Nominatim** — turns an address into lat/lon (geocoding).
- **Overpass** — finds points of interest near a lat/lon, filtered by category.

> ⚠️ **Usage etiquette:** Nominatim and Overpass are free community servers. Always send a descriptive `User-Agent` header, and don't hammer them — cache results during testing. If they feel slow/fiddly, the Plan B is **Geoapify Places** (also OSM data, cleaner JSON, free tier, needs a free key). Decide with the team at the checkpoint.

Quick smoke test before you build anything — confirm geocoding works:

```python
import requests
r = requests.get(
    "https://nominatim.openstreetmap.org/search",
    params={"q": "Allenby 29, Tel Aviv", "format": "json", "limit": 1},
    headers={"User-Agent": "walking-tour-agent/0.1 (student project)"},
    timeout=10,
)
hit = r.json()[0]
print(hit["lat"], hit["lon"], hit["display_name"])
```

If you get a lat/lon near Tel Aviv, your data source works. **That's your Day-1 milestone** — learn it on day one, not during integration.

---

## Step 2 — Map your interest buttons to OSM tags (Jun 23)

OSM tags places with `key=value` pairs. Your job is to translate the team's interest categories into OSM filters. This mapping lives at the top of `tools.py`:

```python
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
```

> OSM coverage is uneven — `music` and `architecture` are tagged inconsistently. That's fine for an MVP; just note it in the docs. If a category returns nothing, your error path (and Chavi's) handles it gracefully.

---

## Step 3 — Build `get_nearby_places` (Jun 23–25) ❤️ the heart of the data side

It does three things: geocode the address → query Overpass for matching spots near that point → return them as `Place` objects.

Create `tools.py`:

```python
import requests
from contracts import Place, INTERESTS

HEADERS = {"User-Agent": "walking-tour-agent/0.1 (student project)"}
NOMINATIM = "https://nominatim.openstreetmap.org/search"
OVERPASS = "https://overpass-api.de/api/interpreter"

CATEGORY_OSM = { ... }  # the dict from Step 2

def geocode(address):
    """Address -> (lat, lon). Raises ValueError if not found."""
    r = requests.get(NOMINATIM,
                     params={"q": address, "format": "json", "limit": 1},
                     headers=HEADERS, timeout=10)
    r.raise_for_status()
    hits = r.json()
    if not hits:
        raise ValueError(f"Could not locate address: {address!r}")
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

def get_nearby_places(location, interests, radius_m=800, limit=12):
    lat, lon = geocode(location)
    query = _build_overpass_query(lat, lon, interests, radius_m)
    r = requests.post(OVERPASS, data={"data": query}, headers=HEADERS, timeout=30)
    r.raise_for_status()

    places = []
    for el in r.json().get("elements", []):
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
            seen.add(p.name); unique.append(p)
    return unique[:limit]

def _which_interest(tags, interests):
    """Decide which chosen interest a result belongs to."""
    for interest in interests:
        for key, value in CATEGORY_OSM.get(interest, []):
            if key in tags and (value == "*" or tags[key] == value):
                return interest
    return interests[0] if interests else "history"
```

Try it standalone:

```bash
python -c "from tools import get_nearby_places; \
[print(p.name, '|', p.category) for p in get_nearby_places('Allenby 29, Tel Aviv', ['architecture','music','cafe'])]"
```

You should see real Tel Aviv venues with categories. If a category is empty, that's an OSM coverage gap, not a bug — note it.

---

## Step 4 — Build `order_walking_route` (Jun 24–25)

An unordered list isn't a tour. "Nearest-next" (a greedy walk) is enough for the MVP — no fancy optimization. Start from the address (if given) or the first place, then always hop to the closest unvisited stop.

Add to `tools.py`:

```python
from math import radians, sin, cos, asin, sqrt

def _haversine(a_lat, a_lon, b_lat, b_lon):
    """Distance in metres between two lat/lon points."""
    R = 6371000
    dlat, dlon = radians(b_lat - a_lat), radians(b_lon - a_lon)
    h = sin(dlat/2)**2 + cos(radians(a_lat))*cos(radians(b_lat))*sin(dlon/2)**2
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
```

---

## Step 5 — Test on 3 scenarios (Jun 25)

Catch bad data now, while it's easy to trace. Make a tiny script `test_tools.py`:

```python
from tools import get_nearby_places, order_walking_route

scenarios = [
    ("Allenby 29, Tel Aviv", ["architecture", "music", "art"]),
    ("Rothschild Blvd, Tel Aviv", ["history", "cafe"]),
    ("Jaffa Clock Tower", ["food", "museum", "nature"]),
]
for addr, interests in scenarios:
    places = get_nearby_places(addr, interests)
    route = order_walking_route(places)
    print(f"\n=== {addr} {interests} -> {len(route)} stops ===")
    for p in route:
        print(f"  {p.name} ({p.category})  {p.lat:.4f},{p.lon:.4f}")
```

Eyeball each: Are the names real? Do categories match the buttons? Is the order roughly a sensible walk (no zig-zag across the city)? Fix the mapping or radius until all three look good.

---

## Step 6 — Input validation (Jun 30–Jul 1)

Stop empty or nonsensical requests from ever reaching the agent. Add to `tools.py`:

```python
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
```

Efrat calls this in the UI before invoking Chavi's agent; if it returns `False`, show the message and don't run the agent. This is the cheap guard that prevents garbage-in/garbage-out.

---

## Your definition of done
- `get_nearby_places("Allenby 29, Tel Aviv", [...])` returns real, named places in the `Place` shape.
- `order_walking_route(...)` returns them in a sensible nearest-next order.
- All 3 test scenarios produce reasonable output.
- `validate_request(...)` catches empty address and no-interest cases.

## Handoff notes
- **To Chavi:** both tools return `list[Place]` exactly per `contracts.py`. Geocoding failures raise `ValueError` and empty results return `[]` — your error handling reacts to those.
- **To Efrat:** every `Place` has `lat`/`lon`, so they drop straight onto the map. Use `validate_request()` before calling the agent.
- **Known limit to write in the docs:** OSM coverage for `music`/`architecture` is patchy; some categories may return few results in quiet areas.
