"""Chavi's agent core — the walking-tour guide agent.
 
Flow:
  1. Build the system prompt (6 components).
  2. Run the ReAct loop: LLM decides which tool to call, we call it, feed result back.
  3. Return the final JSON tour to the caller (Efrat's UI).
"""
 
import json
import logging
import requests
from dataclasses import asdict
 
from groq import Groq
 
from config import GROQ_API_KEY, MODEL, MAX_STEPS
from models.contracts import Place
from tools import get_nearby_places, order_walking_route
 
# ── Logging setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)
 
# ── Groq client ───────────────────────────────────────────────────────────────
client = Groq(api_key=GROQ_API_KEY)
 
# ── System prompt (6 components) ─────────────────────────────────────────────
SYSTEM_PROMPT = """You are a warm, knowledgeable local walking-tour guide.
 
ROLE: A friendly expert who knows every street, café, and hidden gem in the city.
 
GOAL: Build a short, enjoyable walking tour based on the user's starting address and interests.
 
CONTEXT: The user gives you a starting address and a list of interest categories.
You use tools to find real nearby places and arrange them in a walkable order.
 
TOOLS:
- get_nearby_places: call this FIRST to find real places near the address.
- order_walking_route: call this SECOND to sort the places into a sensible walking order.
Always call both tools — in that order — before writing the tour.
 
RULES:
1. Only include places returned by get_nearby_places — never invent stops.
2. Aim for 4–6 stops total.
3. Each stop gets exactly one friendly, informative sentence of narration.
4. If get_nearby_places returns an error or empty list, tell the user kindly using the error message provided.
5. Never call a tool more than once unless the first call returned an empty list.
 
OUTPUT FORMAT — respond ONLY with valid JSON, exactly like this:
{
  "intro": "A short friendly sentence about the walk.",
  "stops": [
    {
      "name": "Place name",
      "category": "category",
      "lat": 0.0,
      "lon": 0.0,
      "narration": "One friendly sentence about this stop."
    }
  ]
}
 
If there are no stops available, respond with:
{
  "intro": "friendly explanation of the problem",
  "stops": []
}
"""
 
# ── Tool schemas ──────────────────────────────────────────────────────────────
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "get_nearby_places",
            "description": "Find real places near a given address that match the chosen interests.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The starting address, e.g. 'Allenby 29, Tel Aviv'"
                    },
                    "interests": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of interest categories, e.g. ['cafe', 'history']"
                    }
                },
                "required": ["location", "interests"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "order_walking_route",
            "description": "Sort a list of places into the most walkable order (nearest-next).",
            "parameters": {
                "type": "object",
                "properties": {
                    "places": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name":     {"type": "string"},
                                "category": {"type": "string"},
                                "lat":      {"type": "number"},
                                "lon":      {"type": "number"},
                                "blurb":    {"type": "string"}
                            },
                            "required": ["name", "category", "lat", "lon"]
                        },
                        "description": "The list of Place objects returned by get_nearby_places."
                    }
                },
                "required": ["places"]
            }
        }
    }
]
 
# ── Tool wrappers ─────────────────────────────────────────────────────────────
def _run_get_nearby_places(location: str, interests: list[str]) -> str:
    log.info("Tool call → get_nearby_places(location=%r, interests=%s)", location, interests)
    try:
        places = get_nearby_places(location, interests)
        log.info("Tool result → %d places found", len(places))
        if not places:
            log.warning("No places found for %r with interests %s", location, interests)
            return json.dumps({
                "error": "no_results",
                "message": (
                    f"No places found near '{location}' for interests {interests}. "
                    "Try a more central address or different interests."
                )
            })
        return json.dumps([asdict(p) for p in places])
    except ValueError as e:
        log.warning("Geocoding failed: %s", e)
        return json.dumps({
            "error": "bad_address",
            "message": f"Could not find the address '{location}'. Please check the address and try again."
        })
    except requests.exceptions.Timeout:
        log.error("Overpass API timed out")
        return json.dumps({
            "error": "timeout",
            "message": "The map service is taking too long to respond. Please try again in a moment."
        })
    except requests.exceptions.RequestException as e:
        log.error("Overpass API error: %s", e)
        return json.dumps({
            "error": "api_error",
            "message": "Could not reach the map service. Please check your connection and try again."
        })
 
 
def _run_order_walking_route(places: list[dict]) -> str:
    log.info("Tool call → order_walking_route(%d places)", len(places))
    place_objects = [Place(**p) for p in places]
    ordered = order_walking_route(place_objects)
    log.info("Tool result → route with %d stops", len(ordered))
    return json.dumps([asdict(p) for p in ordered])
 
 
tools_map = {
    "get_nearby_places":   _run_get_nearby_places,
    "order_walking_route": _run_order_walking_route,
}
 
# ── Agent loop ────────────────────────────────────────────────────────────────
def run_agent(location: str, interests: list[str]) -> dict:
    """Run the walking-tour agent. Returns the final tour as a dict."""
 
    user_message = (
        f"Build me a walking tour starting at '{location}'. "
        f"I'm interested in: {', '.join(interests)}."
    )
 
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_message},
    ]
 
    log.info("Agent started | location=%r interests=%s", location, interests)
 
    for step in range(MAX_STEPS):
        log.info("── Step %d ──", step + 1)
 
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools_schema,
            tool_choice="auto",
            parallel_tool_calls=False,
        )
 
        msg = response.choices[0].message
 
        # ── No tool call → LLM is ready to answer ────────────────────────
        if not msg.tool_calls:
            log.info("Agent finished — returning final answer")
            try:
                return json.loads(msg.content)
            except json.JSONDecodeError:
                log.error("LLM returned non-JSON: %s", msg.content)
                return {"error": "Agent returned an unexpected response.", "raw": msg.content}
 
        # ── Tool calls ────────────────────────────────────────────────────
        messages.append(msg)
 
        for tool_call in msg.tool_calls:
            func_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
 
            log.info("Action: %s | args: %s", func_name, args)
 
            result = tools_map[func_name](**args)
 
            log.info("Observation: %s", result[:200] if len(result) > 200 else result)
 
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })
 
    log.warning("Max steps (%d) reached without a final answer", MAX_STEPS)
    return {"error": "The agent could not complete the tour. Please try again."}