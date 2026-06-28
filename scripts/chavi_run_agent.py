"""Quick test — run the agent on one scenario and print the result."""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from agent import run_agent

# ── Test scenario ──────────────────────────────────────────────────────
ADDRESS = "Rothschild Blvd, Tel Aviv"
INTERESTS = ["cafe", "history", "architecture"]
# ───────────────────────────────────────────────────────────────────────

print(f"Running agent for: {ADDRESS!r} | interests: {INTERESTS}")
print("-" * 60)

result = run_agent(ADDRESS, INTERESTS)

print("\n── Final Tour ──")
print(json.dumps(result, indent=2, ensure_ascii=False))