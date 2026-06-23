# Project Plan — Walking-Tour Guide Agent
**Course:** Data Science & AI — AI Agents Final Project
**Team:** Chavi · Tzvia · Efrat
**Today:** Sun, June 21, 2026 · **Teacher checkpoint:** Sun, June 28 · **Final due:** Sun, July 5

---

## 1. What we're building

An **AI agent that acts as a local walking-tour guide.** The user types a starting address and taps a few interest buttons — for example *Allenby 29* with *architecture, music, art* — and the agent builds a **personalized walking tour**: an ordered list of nearby stops, each with a sentence of friendly narration, drawn on a map. The user can refine it in chat ("shorter," "more cafés," "skip museums") and the agent rebuilds the tour.

---

## 2. How it works (so the steps make sense)

Four pieces fit together:

- **The agent** — an LLM that, given the request, decides which tools to call and writes the final narrated tour.
- **Two tools** — `get_nearby_places(location, interests)` finds matching spots near the address; `order_walking_route(places)` puts them in a walkable order.
- **The system prompt** — the instruction sheet that tells the agent how to behave (six components: role, goal, context, tools, rules, output format).
- **The app** — a Streamlit screen with the address line, interest buttons, the itinerary, and a simple map.

This maps directly onto the rubric: **2 tools · a 6-component system prompt · documentation · one bonus (error handling).**

---

## 3. Scope — deliberately minimal

Built to meet the rubric and stop there. Explicit non-goals, so we don't drift into extra work:

- **Typed address only** for the starting point (no live GPS).
- **Exactly 2 tools.**
- **One bonus: error handling.**
- **Proximity-ordered route** (nearest-next; no fancy optimization).
- **One demo city** — Tel Aviv / Jaffa.
- **Simple map** — show the stops and the path; no turn-by-turn.

**Definition of "done" for the MVP:** the user enters an address, taps a few interests, and gets 4–6 ordered stops with one-line narration on a map — reliably, three times in a row.

---

## 4. Roles

Each person owns a clear area. Everyone tests, joins the demo, and helps with the deck.

| Owner | Area |
|---|---|
| **Chavi** | Agent core — the agent loop, LLM tool-calling, the 6-component system prompt, integration; adds the error-handling bonus |
| **Tzvia** | Tools & data — the two tools, the places-API setup, input validation |
| **Efrat** | App & docs — the Streamlit interface (address, interest buttons, itinerary, map), the documentation + reflection write-up, and the deck |

**Why this split works:** once the tool signatures and the `Place` schema are frozen on Day 1, Chavi can build against stub tools, Tzvia can build the tools against the schema, and Efrat can build the UI against a stub agent — three parallel tracks that converge.

---

## 5. Timeline & steps (with explanations)

**Working rhythm:** weekday evenings ≈ 2 h/person. **No work Friday evening or Saturday (Shabbat).** The two **Friday daytimes (Jun 26 and Jul 3)** — everyone off their day jobs, before Shabbat — are the main contiguous build blocks; wrap each by mid-afternoon. Deadlines sit on Thu/Fri, with Sunday as buffer.

| Phase | Dates | Focus |
|---|---|---|
| 0 — Setup | Jun 21–22 | Decisions + scaffolding |
| 1 — Core MVP | Jun 23–26 | Build the working tour |
| ⭐ Checkpoint | Jun 28 | Demo to teacher |
| 2 — Harden | Jun 29–Jul 2 | Robustness + bonus + write-ups |
| 3 — Polish | Jul 3 | Deck + rehearsal |
| Submit | Jul 5 | Final checklist |

### Phase 0 — Setup & alignment · Sun Jun 21 – Mon Jun 22
*Goal: lock the shared decisions so nobody is blocked later.*

**Create the repo, shared doc, and API keys; decide the places API** — *Chavi · Jun 22*
Set up one Git repository, a shared planning doc, and the accounts/keys for the LLM and the maps/places API. The key decision is *which* places API — pick a free, low-friction one, because both tools depend on it. A settled API choice and a shared repo prevent "works on my machine" problems later.

**Freeze the tool signatures + the `Place` schema (`contracts.py` v1)** — *Chavi · Jun 22*
Write down the exact names, inputs, and outputs of the two tools, plus the exact fields of a "place" record — and agree not to change them without a quick team vote. This is the most important step: once the contract is fixed, the three of you can build independently against it instead of constantly blocking each other.

**Get geocoding working and confirm the API returns good results** — *Tzvia · Jun 23*
Geocoding means turning a typed address ("Allenby 29") into the latitude/longitude the API needs. Test a few real addresses and check the nearby results make sense. If the data source or geocoding is weak, nothing downstream works — better to learn that on day one than during integration.

**Agree the one demo scenario** — *All · Jun 22*
Pick the single example you'll build and test against — e.g., "Allenby 29; architecture + music + art; 90 minutes." A shared target keeps everyone aimed at the same thing and gives you a consistent way to judge whether it works.

### Phase 1 — Build the core MVP · Tue Jun 23 – Fri Jun 26
*Goal: a working tour, end to end, by Friday afternoon.*

**Agent loop + LLM tool-calling (against stub tools)** — *Chavi · Jun 24*
The agent loop is the cycle where the model reads the request, calls a tool, reads the result, and decides what to do next — until it has an answer. Build it against fake "stub" tools that return canned data, so you're not blocked waiting on the real ones. This is the brain of the app and the core technical milestone.

**Draft the 6-component system prompt** — *Chavi · Jun 25*
The system prompt shapes the agent's behavior. Fill in the six components: role ("a warm local guide"), goal ("a short walkable tour"), context (the address + interests), tools (when to use each), rules ("only use places the tool returned; 4–6 stops"), and output format. Most of the agent's quality and consistency comes from this prompt, not the code.

**Add logging of tool calls and decisions** — *Chavi · Jun 25*
Record each time the agent calls a tool and what it chose. When the agent misbehaves, logs are how you see *why* — and they're the raw material for your reflection and "Solutions" slides.

**Build `get_nearby_places` (geocode + places API)** — *Tzvia · Jun 25*
The first tool: take the address + chosen interests, geocode the address, query the places API for matching nearby spots, and return them in the frozen `Place` shape. This is where the user's interest buttons turn into real places — the heart of the data side.

**Build `order_walking_route` (nearest-next)** — *Tzvia · Jun 25*
The second tool: take the chosen places and order them so each next stop is the closest unvisited one. An unordered list isn't a tour; this is what makes the walk actually walkable.

**Test the tools on 3 sample scenarios** — *Tzvia · Jun 25*
Run both tools on three different address+interest combinations and eyeball the output. This catches bad data and edge cases now, while they're easy to trace — not during integration.

**Streamlit UI: address line + interest buttons → itinerary** — *Efrat · Jun 25*
Build the screen the user touches: a text box for the address, buttons for interests, optionally a time-budget choice, and an area showing the stops. Buttons (rather than free text) keep input clean and map directly onto the tool's categories.

**Simple route map display** — *Efrat · Jun 25*
Plot the ordered stops on a map with the path between them (a lightweight map library does this in a few lines). The map is the demo's "wow" and makes the tour instantly understandable.

**Integration: wire the end-to-end happy path** — *All · Fri Jun 26 (day)*
Connect the real UI → agent → real tools → map so one full request works start to finish. Do this together in the Friday daytime block, because parts that work alone often break when joined — this is where you find and fix the seams. Wrap before Shabbat.

**Dry-run the demo 3×** — *All · Fri Jun 26 (day)*
Run the agreed scenario three times in a row and confirm it works each time. "Worked once" isn't reliable; the checkpoint demo needs to be repeatable.

*Sat Jun 27 — off (Shabbat).*

### ⭐ Checkpoint — Sun Jun 28 (teacher session)
**Demo the working happy path; collect feedback and questions.**
Walk the teacher through the agreed scenario live, show the system prompt and the two tools, and bring a short list of questions (Is the scope right? Is this the "6 components" you expect? Which places API do you recommend if ours is flaky? Is the final presentation date clear of Shabbat?). Mid-point feedback is cheap to act on now and expensive to ignore later — turn it into tasks the same evening.

### Phase 2 — Harden · Mon Jun 29 – Thu Jul 2
*Goal: make it robust, add the bonus, and start the write-ups.*

**Incorporate teacher feedback (priorities first)** — *All · Jun 30*
Convert the checkpoint notes into tasks and do the highest-impact ones first. Acting visibly on feedback is usually rewarded and stops small issues from growing.

**Error-handling bonus: no results / bad address / API failure** — *Chavi · Jul 1*
Handle the cases that break a naive version: an address the geocoder can't find, an area with nothing nearby, the API timing out — each with a friendly message and a sensible fallback (e.g., widen the search). This is your chosen bonus and exactly the resilience graders look for.

**Tighten the system prompt + test edge cases** — *Chavi · Jul 2*
Refine the wording so the agent behaves consistently, and probe odd inputs (no interest selected, a tiny time budget). Small prompt tweaks fix most "it's inconsistent" complaints.

**Input validation (address present? interests chosen?)** — *Tzvia · Jul 1*
Before calling the agent, check the user actually entered an address and picked at least one interest, and nudge them if not. This stops empty or nonsensical requests from reaching the agent and producing garbage.

**Draft the documentation (what it does / works / doesn't)** — *Efrat · Jul 1*
Write the honest project doc the rubric asks for, including current limitations. It's required — and being candid about what doesn't work reads as maturity, not weakness.

**Draft reflection answers + start the deck** — *Efrat · Jul 2*
Answer the reflection questions (tools used, what was challenging, where it gets stuck, what you'd change) and begin the slides. Pulling this earlier protects you, because the final Friday is a short day.

**Bug-bash: try to break each other's parts** — *All · Jul 2*
Each person deliberately stress-tests someone else's component. Fresh eyes find bugs the author is blind to.

**Code freeze + final end-to-end test** — *All · Jul 2*
Stop adding features and confirm the whole flow still works. Freezing early leaves Friday for polish rather than firefighting, and keeps a known-good version safe.

### Phase 3 — Polish & deck · Fri Jul 3 (daytime only)
*Goal: finishing touches; wrap before Shabbat.*

**Finalize the deck + record a backup demo video** — *Efrat + team · Fri Jul 3 (day)*
Complete the slides (Idea → Requirements → Reflection → Solutions) and record a short screen capture of the working demo. The recording is your insurance if the live demo or WiFi fails on the day.

**Rehearse the presentation** — *All · Fri Jul 3 (day)*
Run through who says what, end to end, once or twice. A smooth, on-time presentation is part of the grade and steadies nerves.

*Sat Jul 4 — off (Shabbat).*

### Submit — Sun Jul 5
**Final deliverables-checklist pass + submit** — *All · Jul 5*
Tick off every rubric item and submit. The code is already frozen, so this is a calm buffer day for a clean handoff.

---

## 6. Risks & solutions (keep notes as you go — this becomes the "Solutions" slide)

| Problem | Why it happens | Solution |
|---|---|---|
| Agent invents a place | The model fills gaps from memory | Rule: "only use places from the tool"; validate output against tool results |
| No results nearby | Quiet area or narrow interests | Widen the search radius, then a friendly "try a more central spot" |
| Tour too long / scattered | No limit on stops | Cap stops and walking time in the prompt; nearest-next ordering |
| Agent loops | No stop condition | Hard cap (~5) on tool-call rounds |
| Inconsistent answers | Vague prompt | More specific prompt; fixed output format; low temperature |
| Hard to debug | No visibility | Log every tool call and the agent's reasoning |
| API quota / failure | Key limit or outage | Catch errors, retry once, cache the last good result for the demo |

---

## 7. Deliverables checklist (maps to the grade)

- [ ] Agent with **2 working tools** (`get_nearby_places`, `order_walking_route`)
- [ ] **System prompt with all 6 components** (documented)
- [ ] **Error handling** (the bonus)
- [ ] **Documentation:** what it does · what works · what doesn't
- [ ] **Reflection** answers (tools used · what the agent does · what was challenging · what worked · where it gets stuck · how errors were handled · what surprised us · what we'd do differently)
- [ ] **Presentation deck** (Idea → Requirements → Reflection → Solutions)
- [ ] Demo works live **and** a backup recording exists
- [ ] Code in the repo, runnable from a clean clone with a short README

---

## 8. Working agreements

- **Async-first:** a short daily written check-in (done / blockers) in the group chat.
- **One 30-min sync** right after the Jun 28 checkpoint to re-plan from feedback.
- **Freeze interfaces early** (tool signatures + `Place` schema on Day 1) so work stays parallel.
- **Scope guard:** if anything threatens the Jun 26 happy-path demo, cut it — and resist adding features beyond the rubric.
