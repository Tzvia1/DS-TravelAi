"""
Walking-Tour Guide — Streamlit UI  (Efrat's part)
=================================================

The only part of the project the user actually sees and touches:
address line -> interest buttons -> narrated itinerary -> route map.

How the pieces connect (the frozen contract):
    run_agent(address, interests, note) -> JSON string / dict:
        {
          "intro": "one friendly sentence about the walk",
          "stops": [
            {"name", "category", "lat", "lon", "narration"}
          ]
        }

Run it from the repo root:
    streamlit run app.py

Develop the whole UI with NO agent and NO API key:
    USE_FAKE_AGENT=1 streamlit run app.py      (macOS / Linux)
    set USE_FAKE_AGENT=1 && streamlit run app.py   (Windows cmd)
"""
import os

import streamlit as st

# Streamlit Cloud only exposes secrets via st.secrets, not os.environ, but
# agent.py reads the key with os.getenv() (for local .env compatibility).
# Bridge the two so the same code works in both places.
if "OPENAI_API_KEY" in st.secrets:
    os.environ.setdefault("OPENAI_API_KEY", st.secrets["OPENAI_API_KEY"])

from models.contracts import INTERESTS
from app_logic import compose_note, fake_agent, parse_tour, valid_coord

# ---------------------------------------------------------------------------
# Agent wiring
# ---------------------------------------------------------------------------
# Flip this to True (or set env USE_FAKE_AGENT=1) to build/demo the UI with no
# OpenAI key and no running agent — handy before integration and as a fallback
# if the WiFi dies during the live demo.
USE_FAKE_AGENT = os.getenv("USE_FAKE_AGENT", "0").lower() in ("1", "true", "yes")


def call_agent(location, interests, note=""):
    """Build a tour. Uses the fake agent or the real one based on the flag.

    Identical requests are cached for the session, so re-building or refining
    the same address+interests+note returns instantly instead of re-calling
    the (slow) agent.
    """
    key = (location.strip().lower(), tuple(sorted(interests)), (note or "").strip())
    cache = st.session_state.get("tour_cache")
    if cache is not None and key in cache:
        return cache[key]

    if USE_FAKE_AGENT:
        result = fake_agent(location, interests, note)
    else:
        # Imported lazily so the UI still loads if the agent deps aren't installed.
        from agent.agent import run_agent
        result = parse_tour(run_agent(location, interests, note))

    if cache is not None and result and result.get("stops"):
        cache[key] = result
    return result


# ---------------------------------------------------------------------------
# Page + session state
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Walking-Tour Guide", page_icon="🚶")

# A pretty-city photo for the background. Swap this URL for any image you like
# (or a different city). The purple→turquoise gradient sits on top and also acts
# as the fallback if the photo ever fails to load.
CITY_IMAGE_URL = "https://images.unsplash.com/photo-1562351768-f68650f3ec54?auto=format&fit=crop&w=1600&q=70"

# Strength of the purple→turquoise wash over the photo: 0.0 = photo only,
# 1.0 = solid color. Lower it to let the city picture show through more.
TINT_ALPHA = 0.4

st.markdown(f"""
<style>
/* ---- background: purple→turquoise tint over a city photo ---- */
.stApp {{
    background:
        linear-gradient(135deg, rgba(124,58,237,{TINT_ALPHA}), rgba(20,184,166,{TINT_ALPHA})),
        url('{CITY_IMAGE_URL}') center/cover fixed no-repeat;
}}

/* ---- readable content card floating over the photo ---- */
.stMainBlockContainer, .block-container {{
    background: rgba(255, 255, 255, 0.94);
    border-radius: 20px;
    padding: 2rem 2.5rem 2.5rem;
    margin-top: 2rem;
    box-shadow: 0 12px 45px rgba(76, 29, 149, 0.35);
}}

/* ---- headings in purple ---- */
h1, h2, h3 {{ color: #5B21B6 !important; }}

/* ---- buttons: UPPERCASE, rounded, lively ---- */
.stButton > button {{
    text-transform: uppercase;
    letter-spacing: 0.04em;
    font-weight: 700;
    border-radius: 12px;
    border: none;
    transition: filter 0.15s ease, transform 0.05s ease;
}}
.stButton > button:hover {{ filter: brightness(1.08); transform: translateY(-1px); }}

/* interest + refine buttons (secondary) -> turquoise */
.stButton > button[kind="secondary"] {{ background: #14B8A6; color: #ffffff; }}
/* the Build button (primary) -> purple */
.stButton > button[kind="primary"] {{ background: #7C3AED; color: #ffffff; }}
</style>
""", unsafe_allow_html=True)

st.title("🚶 Walking-Tour Guide")
st.caption("Type a starting address, tap a few interests, and get a walkable tour.")

if USE_FAKE_AGENT:
    st.info("Demo mode — using the built-in sample tour (no API key needed).", icon="🧪")

if "interests" not in st.session_state:
    st.session_state.interests = set()
if "tour" not in st.session_state:
    st.session_state.tour = None
if "last_address" not in st.session_state:
    st.session_state.last_address = ""
if "last_duration" not in st.session_state:
    st.session_state.last_duration = None
if "tour_cache" not in st.session_state:
    st.session_state.tour_cache = {}

# ---------------------------------------------------------------------------
# Inputs: address + interest buttons + duration
# ---------------------------------------------------------------------------
address = st.text_input("Starting address", placeholder="Allenby 29, Tel Aviv")

st.write("Interests:")
cols = st.columns(4)
for i, interest in enumerate(INTERESTS):
    selected = interest in st.session_state.interests
    label = ("✅ " if selected else "") + interest
    if cols[i % 4].button(label, key=f"btn_{interest}", use_container_width=True):
        # Streamlit reruns the script on every click, so we toggle in state.
        st.session_state.interests.discard(interest) if selected \
            else st.session_state.interests.add(interest)
        st.rerun()

# Tour duration — a slider over a range of minutes. The value is passed to the
# agent through its note field (the contract has no duration param), so no
# change to Chavi's run_agent() signature is needed.
duration = st.slider(
    "Tour duration (minutes)",
    min_value=15, max_value=180, value=60, step=15,
    key="duration",
    help="Roughly how long you'd like to be walking. ~20 min per stop.",
)

# ---------------------------------------------------------------------------
# Build the tour
# ---------------------------------------------------------------------------
if st.button("Build my tour", type="primary"):
    interests = sorted(st.session_state.interests)

    # Tzvia's guard — validate BEFORE calling the agent.
    from tools import validate_request
    ok, msg = validate_request(address, interests)
    if not ok:
        st.warning(msg)
    else:
        with st.spinner("Building your walk..."):
            try:
                tour = call_agent(address, interests, compose_note(duration))
            except Exception:
                tour = None
            if tour and tour.get("stops"):
                st.session_state.tour = tour
                st.session_state.last_address = address
                st.session_state.last_duration = duration
            elif tour is not None:
                # Agent returned a polite "no tour" payload (bad address / no
                # results / API down). Show its message instead of a crash.
                st.session_state.tour = None
                st.warning(tour.get("intro",
                           "Couldn't build a tour. Try a more central address "
                           "or wider interests."))
            else:
                st.session_state.tour = None
                st.error("Sorry — couldn't build a tour. Please try again.")


# ---------------------------------------------------------------------------
# Render itinerary + map
# ---------------------------------------------------------------------------
tour = st.session_state.tour
if tour:
    st.subheader("Your tour")
    n_stops = len(tour.get("stops", []))
    if st.session_state.last_duration:
        st.caption(f"🕒 ~{st.session_state.last_duration} min · {n_stops} stops")
    if tour.get("intro"):
        st.write(tour["intro"])

    for n, stop in enumerate(tour.get("stops", []), 1):
        st.markdown(f"**{n}. {stop.get('name', '?')}**  ·  _{stop.get('category', '')}_")
        if stop.get("narration"):
            st.write(stop["narration"])

    # ---- route map (the demo "wow") --------------------------------------
    mappable = [s for s in tour.get("stops", []) if valid_coord(s)]
    if mappable:
        try:
            import folium
            from streamlit_folium import st_folium

            center = [float(mappable[0]["lat"]), float(mappable[0]["lon"])]
            fmap = folium.Map(location=center, zoom_start=15)

            coords = []
            for n, stop in enumerate(mappable, 1):
                lat, lon = float(stop["lat"]), float(stop["lon"])
                coords.append((lat, lon))
                folium.Marker(
                    [lat, lon],
                    popup=f"{n}. {stop.get('name', '')}",
                    tooltip=f"{n}. {stop.get('name', '')}",
                    icon=folium.Icon(color="blue", icon="info-sign"),
                ).add_to(fmap)

            folium.PolyLine(coords, weight=4, opacity=0.7).add_to(fmap)
            st_folium(fmap, width=700, height=450)
        except ModuleNotFoundError:
            # Zero-styling fallback: plain pins. Keep the demo alive if folium
            # isn't installed.
            import pandas as pd
            st.map(pd.DataFrame(
                [{"lat": float(s["lat"]), "lon": float(s["lon"])} for s in mappable]
            ))

    # ---- refine (nice-to-have) -------------------------------------------
    note = st.text_input("Refine your tour (e.g. 'shorter', 'more cafes', 'skip museums')")
    if st.button("Refine") and note:
        with st.spinner("Rebuilding..."):
            try:
                refined = call_agent(
                    st.session_state.last_address or address,
                    sorted(st.session_state.interests),
                    compose_note(st.session_state.last_duration or duration, note),
                )
            except Exception:
                refined = None
            if refined and refined.get("stops"):
                st.session_state.tour = refined
                st.rerun()
            else:
                st.warning("Couldn't refine that — keeping your current tour.")
else:
    st.write("")  # spacer
    st.caption("👆 Enter an address, pick interests, and press **Build my tour**.")
