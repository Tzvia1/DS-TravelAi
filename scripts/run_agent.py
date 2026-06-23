"""Edit the variables below and run: python scripts/run_agent.py
Needs a real OPENAI_API_KEY in a .env file at the project root.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Avoid UnicodeEncodeError on Windows consoles when venue names are in Hebrew.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from agent.agent import run_agent

# ----- fill these in -----------------------------------------------------
ADDRESS = "Anilevitch 70 Bnei Brak"  # e.g. "Rothschild Blvd 10 Tel Aviv"
INTERESTS = ["architecture", "food", "art"]
NOTE = ""  # e.g. "shorter", "more cafes", "skip museums"
# --------------------------------------------------------------------------

raw = run_agent(ADDRESS, INTERESTS, NOTE)

try:
    tour = json.loads(raw)
except (json.JSONDecodeError, TypeError):
    print("-> Model did not return valid JSON. Raw output:")
    print(raw)
else:
    print(tour.get("intro", ""))
    for n, stop in enumerate(tour.get("stops", []), 1):
        print(f"  {n}. {stop['name']} ({stop['category']})  {stop['lat']:.5f},{stop['lon']:.5f}")
        print(f"     {stop['narration']}")
