# Efrat's part — App & Docs

Scope: the Streamlit interface (address line, interest buttons, duration slider,
itinerary, route map), the project documentation, and the deck.
(See [docs/Guide_Efrat_App_Docs.md](docs/Guide_Efrat_App_Docs.md) for the full spec.)
This is the only part the user actually sees and touches. It renders the dict
the agent returns — no business logic of its own beyond presentation.

## Files

| File | Purpose |
|---|---|
| `app.py` | The Streamlit screen: address + interest buttons + duration slider → itinerary → route map, plus an optional refine box |
| `app_logic.py` | Pure, UI-free logic (`parse_tour`, `compose_note`, `fake_agent`, `valid_coord`) — split out so it can be unit-tested without Streamlit |
| `tests/test_app_unit.py` | Fast, offline tests for everything in `app_logic.py` |
| `RUN_GUIDE.md` | Full run instructions — local (recommended) and Google Colab (via tunnel) |
| `Walking_Tour_Colab.ipynb` | One-click Colab runner for the tools, agent, and app |
| `requirements.txt` | Project deps — I added `streamlit`, `folium`, `streamlit-folium`, `pandas` here |

## Setup

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
# edit .env and paste a real OPENAI_API_KEY
```

## Running the app

```bash
# the real thing — needs OPENAI_API_KEY in .env
streamlit run app.py               # opens http://localhost:8501

# demo / dev mode — NO key, NO agent, uses a built-in sample tour
USE_FAKE_AGENT=1 streamlit run app.py
#   Windows: set USE_FAKE_AGENT=1 && streamlit run app.py
```

`USE_FAKE_AGENT=1` lets me build the whole UI before integration and is the
backup if the WiFi or API dies during the live demo. Full local + Colab steps
are in [RUN_GUIDE.md](RUN_GUIDE.md).

## Running the tests

```bash
# fast, offline — no key, no network
pytest tests/test_app_unit.py -v
```

They cover the duration→stops mapping, parsing the agent's reply (including
```json fences and prose-wrapped JSON), coordinate validation, and the demo
fake agent.

## How duration is wired

The frozen `run_agent(location, interests, user_note)` has no duration parameter,
so the slider value travels to the agent through the **note** field
(`compose_note(...)` → "Aim for roughly 60 minutes of walking total."). Chavi's
prompt + agent read that and size the walk via the shared `minutes_to_stops`
(4 stops for an hour, up to 6 for longer walks). The UI caption and the agent therefore always agree.

## What it does · what works · what doesn't

**What it does:** address + interests + a duration in → an ordered, narrated
walking tour drawn on a map out, with optional chat refinement.

**What works**
- Address line, 8 interest toggle-buttons, and a 15–180 min duration slider.
- Validates input via `validate_request` before the agent is called.
- Renders the itinerary and a folium route map (markers + walking path).
- Survives bad agent output (fenced/garbled JSON) and bad coordinates without crashing.
- Demo (fake-agent) mode runs the full UI with no key.
- Offline unit tests for all app logic (`pytest tests/test_app_unit.py`).

**What doesn't (yet) — honest limits**
- Typed address only (no live GPS).
- Duration is a target, not a guarantee — a quiet area may yield fewer stops than requested.
- OSM coverage is patchy for some categories (e.g. music venues).
- Route is nearest-next, not truly optimal.
- One demo region (Tel Aviv / Jaffa).
- Streamlit widgets are verified manually; only the pure logic is unit-tested.

## Still to do (my remaining tasks)
- Documentation polish + the 9 reflection answers (see the guide).
- The slide deck (Idea → Requirements → Reflection → Solutions).
- A 1–2 min backup demo video.

## Handoff
- **From Chavi:** `run_agent(...)` returns a JSON **string** → `parse_tour()` turns it into `{"intro", "stops":[{name,category,lat,lon,narration}]}`.
- **From Tzvia:** call `validate_request(address, interests)` before the agent; every stop has `lat`/`lon` for the map.
- **Shared:** `app.py` depends on `app_logic.py` — keep both at the repo root.
