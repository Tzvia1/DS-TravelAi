# Walking-Tour Guide Agent

An AI agent that acts as a local walking-tour guide: give it a starting
address and a few interests (architecture, art, music, history, food, cafe,
museum, nature), and it builds a short, narrated, walkable tour using real
places from OpenStreetMap.

**Team:** Chavi (agent core) · Tzvia (tools & data) · Efrat (app & docs).
Full spec: [docs/Walking_Tour_Agent_Project_Plan.md](docs/Walking_Tour_Agent_Project_Plan.md).

## How it works

```
address + interests
        │
        ▼
   agent/agent.py  ──calls──▶  tools.py
   (LLM tool-calling loop)     (get_nearby_places, order_walking_route)
        │                            │
        ▼                            ▼
   JSON tour                  models/contracts.py
   {intro, stops[]}            (shared Place schema)
```

- **`tools.py`** — geocodes the address and fetches/orders real nearby places via OpenStreetMap (Nominatim + Overpass). No API key needed.
- **`agent/`** — the LLM loop that calls those tools and writes the narrated tour, using OpenAI (`gpt-4o-mini`). Needs an `OPENAI_API_KEY`.
- **`models/contracts.py`** — the frozen `Place` schema both sides agree on.
- **Streamlit UI + map** (Efrat's part) — not built yet.

## Project layout

| Path | Owner | What's there |
|---|---|---|
| `tools.py`, `tests/`, `scripts/run_tools.py` | Tzvia | Data tools — see [README_Tzvia.md](README_Tzvia.md) |
| `agent/`, `scripts/run_agent.py` | Chavi | Agent loop + prompt — see [README_Chavi.md](README_Chavi.md) |
| `app.py` (not yet built) | Efrat | Streamlit UI + map |
| `models/contracts.py` | Shared | Frozen `Place` schema |
| `docs/` | Shared | Project plan, per-person guides, task tracker |

## Setup (from a clean clone)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# edit .env and add a real OPENAI_API_KEY (with billing/credits enabled)
```

## How to run it yourself

```powershell
.venv\Scripts\activate

# the data tools only — no API key needed, edit ADDRESS/INTERESTS inside
python scripts\run_tools.py

# the full agent (tools + LLM) — needs OPENAI_API_KEY, edit ADDRESS/INTERESTS/NOTE inside
python scripts\run_agent.py

# tests for the data tools
pytest -v
```

Check `agent.log` after running the agent to see every tool call it made and why.

## Current status
- ✅ Data tools (`get_nearby_places`, `order_walking_route`, `validate_request`) — built and tested live.
- ✅ Agent loop, 6-component system prompt, logging, error handling — built; verified up to the OpenAI call (needs a funded `OPENAI_API_KEY` to produce a real tour end-to-end).
- ⬜ Streamlit UI + map — not started.

## Known limitations
- OSM tag coverage is uneven — `architecture`/`music` sometimes return few results.
- One demo region tested so far (Tel Aviv/Jaffa), though the agent's prompt and tools are written to work for any address worldwide.
- No automated tests for the agent loop itself (mocking the LLM was deferred) — verify by running `scripts/run_agent.py`.
