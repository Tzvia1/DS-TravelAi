import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from agent.agent import run_agent

# ── Test scenario ──────────────────────────────────────────────────────
ADDRESS   = "Rothschild Blvd, Tel Aviv"
INTERESTS = ["cafe", "history", "architecture"]
NOTE      = ""  # e.g. "shorter", "more cafes", "skip museums"
# ───────────────────────────────────────────────────────────────────────

print(f"Running agent for: {ADDRESS!r} | interests: {INTERESTS}")
print("-" * 60)

result = run_agent(ADDRESS, INTERESTS, NOTE)

print("\n── Final Tour ──")
print(json.dumps(result, indent=2, ensure_ascii=False))