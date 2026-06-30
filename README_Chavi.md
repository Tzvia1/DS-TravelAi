# Chavi's part — Agent Core

Scope: the agent loop, LLM tool-calling, the 6-component system prompt,
logging, and the error-handling bonus.
(See [docs/Guide_Chavi_Agent_Core.md](docs/Guide_Chavi_Agent_Core.md) for the full spec.)
Wired directly to Tzvia's real `tools.py` — no stub tools needed, since it
already works live against OpenStreetMap.

## Files

| File | Purpose |
|---|---|
| `agent/prompts.py` | The 6-component `SYSTEM_PROMPT` (role/goal/context/tools/rules/output format) |
| `agent/agent.py` | `run_agent(location, interests, user_note)` — the tool-calling loop, error handling, logging |
| `scripts/run_agent.py` | Manual run script — edit `ADDRESS`/`INTERESTS`/`NOTE` and run |
| `.env.example` | Shows the `OPENAI_API_KEY` shape; copy to `.env` (gitignored) and fill in a real key |
| `agent.log` | Created at runtime — every tool call and decision, for debugging and the reflection slides |

## Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# then edit .env and paste a real OPENAI_API_KEY
```

## Running it yourself

```powershell
.venv\Scripts\activate
python scripts\run_agent.py
```

Edit the `ADDRESS` / `INTERESTS` / `NOTE` variables at the top of
`scripts/run_agent.py` and re-run. Check `agent.log` afterward to see every
tool call the model made and why.

## What works
- `run_agent(...)` calls `get_nearby_places` then `order_walking_route` and returns valid JSON with real stops for the demo scenario.
- `agent.log` records every tool call, its arguments, and the final decision.
- The system prompt is city-agnostic — it narrates wherever the address geocodes to, not just Tel Aviv.
- **Duration-aware:** when Efrat's UI passes a duration in the note, `run_agent` parses it and injects an explicit stop target (via the shared `minutes_to_stops` in `models/contracts.py`: 4 stops up to an hour, up to 6 for longer walks); with no duration it defaults to 4–6 stops.

## Error handling (the bonus)
| Case | Behavior |
|---|---|
| Geocoder can't find the address | Friendly error message, no crash |
| Nothing nearby | `no_results` status; model suggests a wider/more central search |
| OSM API times out or errors | One retry, then a friendly apology (logged for debugging) |
| Model returns non-JSON | `scripts/run_agent.py` catches the parse failure and shows the raw text |
| Agent loops without an answer | Hard cap at `MAX_ROUNDS = 5`, friendly fallback JSON |
| Bad input (empty address / no interests) | `validate_request` rejects it before the LLM is even called |

## Known limits
- No automated tests for the agent loop — verification is by running `scripts/run_agent.py` with a real key (mocking the LLM was deferred for now).
- Costs a small amount of real OpenAI API usage per run (gpt-4o-mini is cheap, but not free).

## Handoff
- **To Efrat:** `run_agent(...)` returns a JSON **string** — `json.loads()` it to get `{"intro": str, "stops": [{name, category, lat, lon, narration}]}`.
