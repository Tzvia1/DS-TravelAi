# Tzvia's part — Tools & Data

Scope: `get_nearby_places`, `order_walking_route`, and `validate_request` — the
data layer that turns an address + interest buttons into real, ordered places.
(See [Guide_Tzvia_Tools_Data.md](Guide_Tzvia_Tools_Data.md) for the full spec.)
The overall project README/docs/deck belong to Efrat; this file only covers
running and testing my part.

## Files

| File | Purpose |
|---|---|
| `contracts.py` | Frozen `Place` schema + `INTERESTS` (Chavi owns this for real; bootstrapped here so I'm not blocked) |
| `tools.py` | `geocode`, `get_nearby_places`, `order_walking_route`, `validate_request` |
| `tests/conftest.py` | Lets tests import root-level `tools.py`/`contracts.py` |
| `tests/test_tools_unit.py` | Fast, offline tests (pure logic, no network) |
| `tests/test_tools_live.py` | Hits the real Nominatim/Overpass APIs; skips gracefully if unreachable |
| `tests/manual_scenarios.py` | Prints the 3 demo scenarios for eyeballing real venue names |

## Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
```

(`requirements-dev.txt` includes `requirements.txt` + `pytest`.)

## Running the tests yourself

```powershell
.venv\Scripts\activate

# fast, offline — run these constantly while coding
pytest tests/test_tools_unit.py -v

# hits real OpenStreetMap APIs — needs internet, a bit slower
pytest tests/test_tools_live.py -v

# everything
pytest -v

# eyeball real results for the 3 agreed demo scenarios
python tests/manual_scenarios.py
```

## What works
- `geocode("Allenby 29, Tel Aviv")` returns correct Tel Aviv coordinates.
- `get_nearby_places(...)` returns real, named places for all 3 demo scenarios.
- `order_walking_route(...)` orders by nearest-next (verified with a synthetic 4-point test, no network needed).
- `validate_request(...)` catches empty address, no interests, and unknown interest names.

## Known limitation
OSM tag coverage is uneven — `architecture` and `music` often return few or no
results (the Allenby scenario mostly surfaces cafés instead). This is a data
source gap, not a bug; `test_order_walking_route_preserves_the_same_places`
skips per-scenario if a category genuinely returns nothing.

## Handoff
- **To Chavi:** both tools return `list[Place]` exactly per `contracts.py`. Geocoding failures raise `ValueError`; empty results return `[]`.
- **To Efrat:** every `Place` has `lat`/`lon` for the map. Call `validate_request()` before invoking the agent.
