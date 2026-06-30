# Walking-Tour Guide Agent

An AI agent that acts as a local walking-tour guide: give it a starting
address and a few interests (architecture, art, music, history, food, cafe,
museum, nature), and it builds a short, narrated, walkable tour using real
places from OpenStreetMap.

**Team:** Chavi (agent core) · Tzvia (tools & data) · Efrat (app & docs).
Full spec: [docs/Walking_Tour_Agent_Project_Plan.md](docs/Walking_Tour_Agent_Project_Plan.md).

## How it works

```
   app.py (Streamlit UI)
   address + interests + duration
        │
        ▼
   agent/agent.py  ──calls──▶  tools.py
   (LLM tool-calling loop)     (get_nearby_places, order_walking_route)
        │                            │
        ▼                            ▼
   JSON tour ───▶ app.py renders    models/contracts.py
   {intro, stops[]}  itinerary + map (shared Place schema)
```

- **`app.py` / `app_logic.py`** — the Streamlit screen the user touches (address line, interest buttons, duration slider, itinerary, route map). Pure logic lives in `app_logic.py` so it can be unit-tested without Streamlit.
- **`tools.py`** — geocodes the address and fetches/orders real nearby places via OpenStreetMap (Nominatim + Overpass). No API key needed.
- **`agent/`** — the LLM loop that calls those tools and writes the narrated tour, using OpenAI (`gpt-4o-mini`). Needs an `OPENAI_API_KEY`.
- **`models/contracts.py`** — the frozen `Place` schema + `INTERESTS`, plus a shared `minutes_to_stops` helper so the UI's duration slider and the agent agree on tour length.

## Project layout

| Path | Owner | What's there |
|---|---|---|
| `tools.py`, `tests/test_tools_*`, `scripts/run_tools.py` | Tzvia | Data tools — see [README_Tzvia.md](README_Tzvia.md) |
| `agent/`, `scripts/run_agent.py` | Chavi | Agent loop + prompt — see [README_Chavi.md](README_Chavi.md) |
| `app.py`, `app_logic.py`, `tests/test_app_unit.py` | Efrat | Streamlit UI + map + docs — see [README_Efrat.md](README_Efrat.md) |
| `models/contracts.py` | Shared | Frozen `Place` schema + `INTERESTS` + `minutes_to_stops` |
| `RUN_GUIDE.md`, `Walking_Tour_Colab.ipynb` | Efrat | Full run instructions (local + Google Colab) |
| `docs/` | Shared | Project plan, per-person guides, task tracker |

## Setup (from a clean clone)

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt    # includes streamlit, folium, streamlit-folium
cp .env.example .env               # Windows: copy .env.example .env
# edit .env and add a real OPENAI_API_KEY (with billing/credits enabled)
```

## How to run it yourself

```bash
# 1) THE APP — the full UI + map (this is the demo)
streamlit run app.py
#    opens http://localhost:8501

#    ...or build/demo the UI with NO key and NO agent (uses a sample tour):
USE_FAKE_AGENT=1 streamlit run app.py          # Windows: set USE_FAKE_AGENT=1 && streamlit run app.py

# 2) the data tools only — no API key needed (edit ADDRESS/INTERESTS inside)
python scripts/run_tools.py

# 3) the full agent (tools + LLM) — needs OPENAI_API_KEY (edit vars inside)
python scripts/run_agent.py
```

Check `agent.log` after running the agent to see every tool call it made and why.
**Running in Google Colab?** See [RUN_GUIDE.md](RUN_GUIDE.md) — the app needs a public
tunnel there, so running locally is the smoother path for the live demo.

## Testing

```bash
# fast, offline — no API key, no network. Run these constantly while coding.
pytest tests/test_app_unit.py tests/test_tools_unit.py -v

# everything, including the live OpenStreetMap tests (needs internet)
pytest -v
```

- `tests/test_tools_unit.py` — Tzvia's data-tool logic (routing, validation, query building).
- `tests/test_app_unit.py` — Efrat's app logic (duration→stops, agent-output parsing, coordinate validation, the demo fake agent).
- `tests/test_tools_live.py` — hits real Nominatim/Overpass; skips gracefully if offline.
- The Streamlit widgets themselves are verified manually (browser-automation wasn't worth the cost at this scope); the agent loop has no automated tests — verify it by running `scripts/run_agent.py`.

## Current status
- ✅ Data tools (`get_nearby_places`, `order_walking_route`, `validate_request`) — built and tested live.
- ✅ Agent loop, 6-component system prompt, logging, error handling — built; duration-aware. Needs a funded `OPENAI_API_KEY` for a real end-to-end tour.
- ✅ Streamlit UI + route map + duration control — built, with offline unit tests and a demo (fake-agent) mode.

## Known limitations
- OSM tag coverage is uneven — `architecture`/`music` sometimes return few results, so a requested long walk may come back shorter if the area is quiet.
- The duration control is honored as a target, not a guarantee — the agent only has as many stops as the data source actually returns.
- One demo region tested so far (Tel Aviv/Jaffa), though the prompt and tools are written to work for any address worldwide.
- No automated tests for the agent loop itself (mocking the LLM was deferred) — verify by running `scripts/run_agent.py`; the Streamlit widgets are verified manually.
