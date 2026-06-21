# Chavi's Guide — Agent Core 🧠

**Your area:** the agent loop, LLM tool-calling, the 6-component system prompt, integration, and the error-handling bonus.
**You also own Day 0 setup** (repo, keys, the frozen contract) because everyone else builds on top of it.

You know Python basics. You do **not** need to have built an "agent" before — this guide explains every piece. An agent here is just: *a loop that lets the LLM call your functions and read the results until it can answer.* That's it.

---

## Your tasks & dates (from the tracker)

| When | Task | Done when… |
|---|---|---|
| Sun–Mon Jun 21–22 | Repo, shared doc, API keys, **pick the places API** | Everyone can clone and run an empty app |
| Mon Jun 22 | **Freeze `contracts.py` v1** (tool signatures + `Place`) | Team agrees; nobody changes it without a vote |
| Tue–Wed Jun 23–24 | Agent loop + tool-calling (against **stub** tools) | Loop calls a fake tool and writes an answer |
| Thu Jun 25 | Draft the **6-component system prompt** | Agent behaves consistently on the demo scenario |
| Thu Jun 25 | Add **logging** of tool calls + decisions | You can read a log and see *why* it did something |
| Fri Jun 26 (day) | **Integration** with real tools + UI (all-hands) | Full request works end-to-end before Shabbat |
| Tue–Wed Jun 30–Jul 1 | **Error-handling bonus** | Bad address / no results / API down all handled |
| Wed–Thu Jul 1–2 | Tighten the prompt + edge cases | No more "it's random" complaints |

---

## Day 0, Step 1 — Repo + structure (Jun 21–22)

Create one Git repo and this exact file layout. Freezing the layout now prevents merge pain later.

```
walking-tour-agent/
├── contracts.py        # YOU own this — the frozen schema + tool signatures
├── stub_tools.py       # YOU — fake tools so you can build before Tzvia is done
├── agent.py            # YOU — the agent loop + tool-calling
├── prompts.py          # YOU — the 6-component system prompt
├── tools.py            # Tzvia — real get_nearby_places / order_walking_route
├── app.py              # Efrat — Streamlit UI + map
├── requirements.txt
├── .env                # secrets — NEVER commit
├── .gitignore
└── README.md
```

Commands:

```bash
mkdir walking-tour-agent && cd walking-tour-agent
git init
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

Create `requirements.txt`:

```
openai>=1.0
python-dotenv
requests
streamlit
folium
streamlit-folium
```

Install: `pip install -r requirements.txt`

Create `.gitignore` (so secrets and junk never get committed):

```
.venv/
.env
__pycache__/
*.pyc
```

Create `.env` (each teammate makes their own; it is **not** committed):

```
OPENAI_API_KEY=sk-...your-key...
```

> **LLM choice:** This guide uses the OpenAI Python SDK because it's the most common in courses and the tool-calling pattern is simple. If your course uses **Anthropic/Claude** instead, the loop is identical — only the SDK call differs (see the note at the end of the agent section). Pick one and tell the team.

---

## Day 0, Step 2 — Decide the places API (Jun 22)

Both of Tzvia's tools depend on this, so decide it on Day 0. **Recommendation: OpenStreetMap — free and needs no API key.**

- **Geocoding** (address → lat/lon): **Nominatim** — free, keyless.
- **Nearby places** (lat/lon + category → spots): **Overpass API** — free, keyless.
- *Friendlier alternative if Overpass feels fiddly:* **Geoapify Places** (uses OSM data, has a clean JSON API and a free tier; needs a free key). Keep this as Plan B and mention it at the checkpoint.

You don't have to build these — Tzvia does. You just **lock the choice** so the contract below is stable. Write the decision in the shared doc.

---

## Day 0, Step 3 — Freeze `contracts.py` (Jun 22) ⭐ most important step

This is the single thing that lets all three of you work in parallel. Once it's frozen, Tzvia builds tools that *return* this shape, Efrat builds a UI that *renders* this shape, and you build an agent that *calls* these signatures — without blocking each other.

Create `contracts.py`:

```python
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
```

Commit this and announce it in the group chat: **"Contract frozen, build away."**

---

## Day 1–2, Step 4 — Stub tools so you're never blocked (Jun 23)

Before Tzvia's real tools exist, write fakes that return the contract shape. Now you can build the whole agent today.

Create `stub_tools.py`:

```python
from contracts import Place

def get_nearby_places(location, interests, radius_m=800, limit=12):
    # Canned data near Allenby 29, Tel Aviv — ignores inputs, just returns a fixed list.
    demo = [
        Place("Bauhaus Center", "architecture", 32.0773, 34.7745, "Hub of White City design."),
        Place("Levontin 7", "music", 32.0648, 34.7766, "Beloved live-music venue."),
        Place("Gordon Gallery", "art", 32.0810, 34.7710, "Contemporary Israeli art."),
        Place("Cafe Xoho", "cafe", 32.0760, 34.7730, "Cosy specialty coffee."),
        Place("Independence Hall", "history", 32.0648, 34.7710, "Where statehood was declared."),
    ]
    chosen = [p for p in demo if p.category in interests] or demo
    return chosen[:limit]

def order_walking_route(places, start_lat=None, start_lon=None):
    return places  # stub: don't bother ordering yet
```

---

## Day 1–2, Step 5 — The agent loop (Jun 23–24) 🧠 core milestone

This is the heart of the project. The pattern is always the same, regardless of LLM:

1. Describe your tools to the model (JSON schemas).
2. Send the user's request + tool list.
3. If the model asks to call a tool → run your Python function, send the result back.
4. Repeat until the model returns a normal answer (with a **hard cap** so it can't loop forever).

Create `agent.py`:

```python
import os, json, logging
from dotenv import load_dotenv
from openai import OpenAI

# Build against stubs first; swap this one line to `import tools` at integration time.
import stub_tools as tools
from prompts import SYSTEM_PROMPT

load_dotenv()
client = OpenAI()  # reads OPENAI_API_KEY from .env
log = logging.getLogger("agent")

MODEL = "gpt-4o-mini"   # any tool-calling model your course allows
MAX_ROUNDS = 5          # hard cap = the "agent loops forever" fix

# --- 1. Describe the tools to the model -------------------------------
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_nearby_places",
            "description": "Find real places near an address that match the user's interests.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "Street address, e.g. 'Allenby 29, Tel Aviv'"},
                    "interests": {"type": "array", "items": {"type": "string"},
                                  "description": "Category keys like ['architecture','music']"},
                },
                "required": ["location", "interests"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "order_walking_route",
            "description": "Put a list of places into a walkable nearest-next order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "places": {"type": "array", "items": {"type": "object"},
                               "description": "The places to order (as returned by get_nearby_places)."},
                },
                "required": ["places"],
            },
        },
    },
]

# --- 2. Map tool names to the real Python functions -------------------
def _call_tool(name, args):
    if name == "get_nearby_places":
        places = tools.get_nearby_places(args["location"], args["interests"])
    elif name == "order_walking_route":
        # places arrive as plain dicts from the model; rebuild Place objects
        from contracts import Place
        objs = [Place(**p) if isinstance(p, dict) else p for p in args["places"]]
        places = tools.order_walking_route(objs)
    else:
        return {"error": f"unknown tool {name}"}
    # return JSON-friendly dicts the model can read
    return [p.__dict__ for p in places]

# --- 3. The loop ------------------------------------------------------
def run_agent(location, interests, user_note=""):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content":
            f"Address: {location}\nInterests: {interests}\nExtra request: {user_note or 'none'}"},
    ]

    for round_num in range(MAX_ROUNDS):
        resp = client.chat.completions.create(
            model=MODEL, messages=messages,
            tools=TOOL_SCHEMAS, tool_choice="auto",
            temperature=0.3,            # low = more consistent
        )
        msg = resp.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            log.info("Final answer after %d round(s).", round_num)
            return msg.content           # the model is done

        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            log.info("TOOL CALL %s args=%s", tc.function.name, args)
            result = _call_tool(tc.function.name, args)
            messages.append({
                "role": "tool", "tool_call_id": tc.id,
                "content": json.dumps(result),
            })

    log.warning("Hit MAX_ROUNDS without a final answer.")
    return "Sorry — I couldn't build a tour this time. Please try again."
```

**Test it right now** (with stubs), before any prompt polish:

```bash
python -c "import logging; logging.basicConfig(level=logging.INFO); \
from agent import run_agent; print(run_agent('Allenby 29, Tel Aviv', ['architecture','music']))"
```

If you see a `TOOL CALL get_nearby_places` line and then a written tour, **the core works.** That's your milestone.

> **Using Claude instead of OpenAI?** Same loop, same `MAX_ROUNDS`, same logging. Differences: tool schemas go in a flatter `tools=[{"name":..., "description":..., "input_schema":{...}}]` shape; you look for `content` blocks of `type == "tool_use"` instead of `msg.tool_calls`; and you send results back as a `user` message containing a `tool_result` block. Pick one SDK and stay on it.

---

## Day 3, Step 6 — The 6-component system prompt (Jun 25)

Most of the agent's quality lives **here**, not in the code. The rubric wants all six components — write them as labelled sections so the grader can see each one.

Create `prompts.py`:

```python
SYSTEM_PROMPT = """
# ROLE
You are a warm, knowledgeable local walking-tour guide for Tel Aviv–Jaffa.

# GOAL
Turn a starting address and a few interests into a short, walkable tour of
4–6 stops, each with one friendly sentence of narration.

# CONTEXT
The user gives a typed address and taps interest buttons (architecture, art,
music, history, food, cafe, museum, nature). They may refine in chat
("shorter", "more cafes", "skip museums") and you rebuild the tour.

# TOOLS
- get_nearby_places(location, interests): call FIRST to fetch real places.
- order_walking_route(places): call SECOND to put them in walking order.
Always call get_nearby_places before writing any tour.

# RULES
- Use ONLY places returned by the tools. Never invent a place or a fact.
- Keep it to 4–6 stops. Order them with order_walking_route.
- One short, friendly sentence per stop. No addresses or coordinates in prose.
- If no places come back, say so kindly and suggest a more central address.

# OUTPUT FORMAT
Return ONLY valid JSON, no markdown fences:
{
  "intro": "one friendly sentence about the walk",
  "stops": [
    {"name": "...", "category": "...", "lat": 0.0, "lon": 0.0,
     "narration": "one friendly sentence"}
  ]
}
""".strip()
```

> Because you ask for JSON, parse the agent's return with `json.loads(...)` before handing it to Efrat's UI. Wrap that parse in `try/except` — if the model ever adds stray text, strip ```` ```json ```` fences first. This becomes part of your error handling.

---

## Day 3, Step 7 — Logging (Jun 25)

You already added `log.info(...)` lines above — now make them visible and saved. At the top of `agent.py`'s `__main__` or in `app.py`'s startup:

```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler("agent.log"), logging.StreamHandler()],
)
```

Now every tool call and decision lands in `agent.log`. When the agent misbehaves, you read the log to see *why* — and these logs are raw material for the **Reflection** and **Solutions** slides ("Hard to debug → add logging").

---

## Fri Jun 26 (day) — Integration (all-hands)

The one-line swap that turns stubs into the real thing:

```python
# in agent.py, change:
import stub_tools as tools
# to:
import tools
```

Then sit together and run the **real** UI → agent → **real** tools → map once, end to end. Parts that work alone often break at the seams (a tool returns a slightly different field, the JSON has an extra key) — fix those together. **Wrap before Shabbat.** Then dry-run the demo scenario 3× in a row; "worked once" isn't ready for the teacher.

---

## Jun 30–Jul 2 — Error-handling bonus + prompt tightening

This is your chosen bonus and exactly what graders reward. Handle the three things that break a naive agent. Most of this is `try/except` around the tool calls inside `_call_tool`, returning a friendly signal the model can act on:

```python
def _call_tool(name, args):
    try:
        if name == "get_nearby_places":
            places = tools.get_nearby_places(args["location"], args["interests"])
            if not places:
                return {"status": "no_results",
                        "message": "No matching places nearby. Suggest a more central address or wider interests."}
            return {"status": "ok", "places": [p.__dict__ for p in places]}
        ...
    except Exception as e:
        log.exception("Tool %s failed", name)
        return {"status": "error",
                "message": "The places service is having trouble. Apologise and suggest trying again."}
```

Cover these cases (and write each into the **Solutions** table as you go):

| Case | What to do |
|---|---|
| Geocoder can't find the address | Friendly "I couldn't locate that address — try adding the city." |
| Nothing nearby | Suggest a wider radius or a more central spot. |
| API times out / quota | Catch, retry **once**, then fall back to the last good result (or a clear apology). |
| Model returns non-JSON | Strip fences, `json.loads`, and if it still fails, ask the model once to "reply with valid JSON only." |

**Then tighten the prompt:** test odd inputs (no interest selected, a tiny time budget, a rural address). Small wording fixes ("exactly 4–6 stops", "JSON only, no prose") cure most "it's inconsistent" complaints. Keep `temperature` low (0.2–0.3).

---

## Your definition of done
- `run_agent(...)` returns valid JSON with 4–6 ordered, real stops for the demo scenario, 3× in a row.
- `agent.log` shows each tool call and decision.
- Bad address / no results / API failure each produce a friendly message, not a crash.
- The 6 components are clearly labelled in `prompts.py` for the grader.

## Handoff notes
- **To Tzvia:** your tools must return `list[Place]` exactly as `contracts.py` defines. I call `get_nearby_places` first, `order_walking_route` second.
- **To Efrat:** I hand you a Python **dict** `{"intro": ..., "stops": [...]}`. Each stop has `name, category, lat, lon, narration`. Render straight from that.
