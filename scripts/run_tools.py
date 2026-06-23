"""Edit the variables below and run: python scripts/run_tools.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Avoid UnicodeEncodeError on Windows consoles when venue names are in Hebrew.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from tools import get_nearby_places, order_walking_route, validate_request

# ----- fill these in -----------------------------------------------------
ADDRESS = "Anilevitch 70 Bnei Brak"
INTERESTS = ["architecture", "food", "art"]
# --------------------------------------------------------------------------

ok, msg = validate_request(ADDRESS, INTERESTS)
if not ok:
    print(f"-> {msg}")
else:
    try:
        places = get_nearby_places(ADDRESS, INTERESTS)
    except ValueError as e:
        places = None
        print(f"-> {e}")

    if places is not None:
        if not places:
            print("-> No matching places found nearby. Try a more central address or different interests.")
        else:
            route = order_walking_route(places)
            print(f"\n{len(route)} stops, in walking order:")
            for n, p in enumerate(route, 1):
                print(f"  {n}. {p.name} ({p.category})  {p.lat:.5f},{p.lon:.5f}")
