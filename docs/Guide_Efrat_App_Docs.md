# Efrat's Guide — App & Docs 🎨

**Your area:** the Streamlit interface (address line, interest buttons, itinerary, map), the documentation + reflection write-up, and the slide deck.
**You build the only part the user actually sees and touches** — and you tell the project's story to the grader. The map is the demo's "wow"; the docs and deck are a big chunk of the grade.

You know Python basics. Streamlit lets you build a web app with pure Python — no HTML/JS needed.

---

## Your tasks & dates (from the tracker)

| When | Task | Done when… |
|---|---|---|
| Tue–Thu Jun 23–25 | **Streamlit UI**: address line + interest buttons → itinerary | The screen the user touches works |
| Thu Jun 25 | **Simple route map** display | Stops + path drawn on a map |
| Fri Jun 26 (day) | Integration (all-hands) | UI wired to the real agent + tools |
| Mon–Wed Jun 29–Jul 1 | **Draft the documentation** (does / works / doesn't) | Honest write-up incl. limits |
| Wed–Thu Jul 1–2 | **Reflection** answers + start the **deck** | All 9 reflection Qs answered; slides begun |
| Fri Jul 3 (day) | Finalize deck + **record backup demo video** | Deck done; video as insurance |

> You can build the whole UI **before** the agent is ready by calling a tiny fake. Don't wait on Chavi or Tzvia.

---

## The contract you render (Chavi owns it)

Chavi's agent hands you a Python **dict**. Build your screen around exactly this shape:

```python
{
  "intro": "A short friendly sentence about the walk.",
  "stops": [
    {"name": "...", "category": "...", "lat": 0.0, "lon": 0.0,
     "narration": "one friendly sentence about this stop"}
  ]
}
```

Interest buttons map to these category keys (from `contracts.py`):
`["architecture", "art", "music", "history", "food", "cafe", "museum", "nature"]`

---

## Step 1 — A stub so you're never blocked (Jun 23)

Before the real agent exists, fake it. Put this at the top of `app.py` and swap to the real import at integration:

```python
def fake_agent(location, interests, note=""):
    return {
        "intro": f"A short walk from {location} for {', '.join(interests)} lovers.",
        "stops": [
            {"name": "Bauhaus Center", "category": "architecture",
             "lat": 32.0773, "lon": 34.7745, "narration": "Heart of the White City design scene."},
            {"name": "Levontin 7", "category": "music",
             "lat": 32.0648, "lon": 34.7766, "narration": "A beloved spot for live music."},
            {"name": "Cafe Xoho", "category": "cafe",
             "lat": 32.0760, "lon": 34.7730, "narration": "Pause here for excellent coffee."},
        ],
    }
```

---

## Step 2 — The Streamlit UI: address + interest buttons → itinerary (Jun 23–25)

Buttons (not free text) keep input clean and map straight onto Tzvia's categories. Streamlit reruns the whole script on every click, so we hold selected interests in `st.session_state`.

Create `app.py`:

```python
import streamlit as st

INTERESTS = ["architecture", "art", "music", "history",
             "food", "cafe", "museum", "nature"]

st.set_page_config(page_title="Walking-Tour Guide", page_icon="🚶")
st.title("🚶 Walking-Tour Guide")
st.caption("Type a starting address, tap a few interests, and get a walkable tour.")

# --- state ---
if "interests" not in st.session_state:
    st.session_state.interests = set()
if "tour" not in st.session_state:
    st.session_state.tour = None

# --- address ---
address = st.text_input("Starting address", placeholder="Allenby 29, Tel Aviv")

# --- interest buttons (toggle on/off) ---
st.write("Interests:")
cols = st.columns(4)
for i, interest in enumerate(INTERESTS):
    selected = interest in st.session_state.interests
    label = ("✅ " if selected else "") + interest
    if cols[i % 4].button(label, key=f"btn_{interest}", use_container_width=True):
        if selected:
            st.session_state.interests.discard(interest)
        else:
            st.session_state.interests.add(interest)
        st.rerun()

# --- build button ---
if st.button("Build my tour", type="primary"):
    interests = list(st.session_state.interests)

    # input validation (Tzvia's function) — guard before calling the agent
    from tools import validate_request
    ok, msg = validate_request(address, interests)
    if not ok:
        st.warning(msg)
    else:
        with st.spinner("Building your walk..."):
            from agent import run_agent          # real agent
            import json
            raw = run_agent(address, interests)
            try:
                st.session_state.tour = json.loads(raw) if isinstance(raw, str) else raw
            except Exception:
                st.error("Sorry — couldn't build a tour. Please try again.")
                st.session_state.tour = None

# --- show itinerary ---
tour = st.session_state.tour
if tour:
    st.subheader("Your tour")
    st.write(tour.get("intro", ""))
    for n, stop in enumerate(tour["stops"], 1):
        st.markdown(f"**{n}. {stop['name']}**  ·  _{stop['category']}_")
        st.write(stop["narration"])
```

> While the agent isn't ready, change `from agent import run_agent` to `run_agent = fake_agent` so you can build the whole screen today.

Run it: `streamlit run app.py` → opens in your browser. Click interests, build, see the list.

---

## Step 3 — The route map (Jun 25) ✨ the demo "wow"

Plot the stops and draw the path between them. We use **folium** (a few lines) embedded with **streamlit-folium**. Add to the bottom of the `if tour:` block:

```python
import folium
from streamlit_folium import st_folium

stops = tour["stops"]
if stops:
    center = [stops[0]["lat"], stops[0]["lon"]]
    fmap = folium.Map(location=center, zoom_start=15)

    coords = []
    for n, stop in enumerate(stops, 1):
        coords.append((stop["lat"], stop["lon"]))
        folium.Marker(
            [stop["lat"], stop["lon"]],
            popup=f"{n}. {stop['name']}",
            tooltip=f"{n}. {stop['name']}",
            icon=folium.Icon(color="blue", icon="info-sign"),
        ).add_to(fmap)

    # the walking path
    folium.PolyLine(coords, weight=4, opacity=0.7).add_to(fmap)
    st_folium(fmap, width=700, height=450)
```

Now the user sees their walk drawn out. This is the moment that makes the tour instantly understandable — give it the most demo time.

*(Optional simplest fallback if folium gives trouble: `st.map(pd.DataFrame(stops)[["lat","lon"]])` shows pins with zero styling. Keep it in your back pocket.)*

---

## Step 4 — Chat refinement (nice-to-have, if time)

The plan mentions "shorter / more cafés / skip museums." A minimal version: a text box whose contents pass to the agent as the extra note.

```python
note = st.text_input("Refine your tour (e.g. 'shorter', 'more cafes')")
if st.button("Refine") and note:
    with st.spinner("Rebuilding..."):
        import json
        raw = run_agent(address, list(st.session_state.interests), note)
        st.session_state.tour = json.loads(raw) if isinstance(raw, str) else raw
        st.rerun()
```

Don't let this block the core demo — it's a bonus on top of the happy path.

---

## Step 5 — Documentation (Jun 29–Jul 1)

The rubric explicitly asks for **"What it does · what works · what doesn't."** Being honest about limits reads as maturity, not weakness. Put this in `README.md` (which also serves as the run-from-clean-clone instructions).

Suggested `README.md` outline:

```markdown
# Walking-Tour Guide Agent

## What it does
One paragraph: address + interests in → an ordered, narrated walking tour on a map out.

## How to run (from a clean clone)
1. `python -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt`
3. Add your `OPENAI_API_KEY` to a `.env` file
4. `streamlit run app.py`

## How it works
- Agent (LLM tool-calling loop) → 2 tools (get_nearby_places, order_walking_route) → Streamlit UI + map.
- 6-component system prompt drives behaviour; tool calls are logged to agent.log.

## What works
- The demo scenario (Allenby 29; architecture/music/art) builds a 4–6 stop tour reliably.
- Map shows stops + path; error handling for bad address / no results / API failure.

## What doesn't (yet) — be honest
- Typed address only (no live GPS).
- OSM coverage is patchy for some categories (e.g. music venues).
- Route is nearest-next, not truly optimal.
- One demo city (Tel Aviv / Jaffa).
```

---

## Step 6 — Reflection answers (Jul 1–2)

The teacher's deck lists **9 reflection questions**. Draft an honest answer to each (keep notes as the team works so this is easy):

1. **What tools did you use?** — the two tools + the LLM + OSM/Streamlit/folium stack.
2. **What does the agent do?** — one clear paragraph.
3. **What was challenging?** — e.g. patchy OSM tags, keeping JSON output clean, the agent inventing places early on.
4. **What worked well?** — the frozen contract enabling parallel work; the map.
5. **Where does the agent get stuck?** — quiet areas, ambiguous addresses, rare interests.
6. **How did you handle the errors?** — Chavi's try/except + retry + friendly fallbacks (pull the Solutions table).
7. **What surprised you?** — your real observation (e.g. how much quality came from the prompt, not the code).
8. **If you started over, what would you do differently?** — honest, specific.
9. *(plus any course-specific extras)*

Pull these answers from the team's daily check-ins and from `agent.log`.

---

## Step 7 — The deck (Jul 1–3)

Match the teacher's structure: **Idea → Requirements → Reflection → Solutions.** Suggested slides:

1. **Title** — project name + team (Chavi, Tzvia, Efrat).
2. **Idea** — the walking-tour agent in one sentence + a screenshot of the map.
3. **Requirements** — ✅ 2 tools · ✅ 6-component prompt · ✅ documentation · ⭐ bonus: error handling.
4. **How it works** — a simple diagram: UI → Agent → 2 Tools → Map.
5. **Reflection** — the highlights from your 9 answers.
6. **Solutions** — the Problem→Solution table (agent loops → iteration cap; inconsistent → specific prompt; bad results → validation; hard to debug → logging).
7. **Demo** — live, with the backup video ready.
8. **Thank you.**

> Need a polished .pptx file built for you? Just ask and I can generate the deck from this outline.

---

## Step 8 — Backup demo video (Jul 3)

Record a 1–2 minute screen capture of a successful run (address → interests → tour → map). This is your **insurance** if the live demo or WiFi fails on the day. Use any screen recorder (QuickTime, OBS, Loom, or your OS's built-in tool). Save it in the repo or shared drive.

---

## Your definition of done
- The Streamlit app: address field + interest buttons + itinerary + map, all working.
- `validate_request` is called before the agent runs.
- `README.md` covers does / works / doesn't and run-from-clean-clone steps.
- All 9 reflection questions answered; deck follows Idea → Requirements → Reflection → Solutions.
- Backup demo video recorded.

## Handoff notes
- **From Chavi:** you receive a dict `{"intro", "stops":[{name,category,lat,lon,narration}]}`. Render straight from it.
- **From Tzvia:** call `validate_request(address, interests)` before invoking the agent; every stop has `lat`/`lon` for the map.
- **To the team:** flag early if any field name in the contract makes rendering awkward — change it by team vote before integration, not after.
