"""Manual eyeball check — prints real results instead of asserting on them.
Run with: python tests/manual_scenarios.py
(Automated pass/fail checks for the same 3 scenarios live in test_tools_live.py.)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import get_nearby_places, order_walking_route

scenarios = [
    ("Allenby 29, Tel Aviv", ["architecture", "music", "art"]),
    ("Rothschild Blvd, Tel Aviv", ["history", "cafe"]),
    ("Jaffa Clock Tower", ["food", "museum", "nature"]),
]
for addr, interests in scenarios:
    places = get_nearby_places(addr, interests)
    route = order_walking_route(places)
    print(f"\n=== {addr} {interests} -> {len(route)} stops ===")
    for p in route:
        print(f"  {p.name} ({p.category})  {p.lat:.4f},{p.lon:.4f}")
