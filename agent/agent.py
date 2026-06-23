import json
import logging
import time

import requests
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

import tools
from models.contracts import Place

from .prompts import SYSTEM_PROMPT

load_dotenv()
client = OpenAI()  # reads OPENAI_API_KEY from .env

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler("agent.log"), logging.StreamHandler()],
)
log = logging.getLogger("agent")

MODEL = "gpt-4o-mini"
MAX_ROUNDS = 5  # hard cap — the "agent loops forever" fix

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
                    "interests": {"type": "array", "items": {"type": "string"}},
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
                    "places": {"type": "array", "items": {"type": "object"}},
                },
                "required": ["places"],
            },
        },
    },
]


def _with_retry(fn, *args, **kwargs):
    """Retry once on a network/HTTP failure (the 'API timing out' bonus case)."""
    try:
        return fn(*args, **kwargs)
    except requests.exceptions.RequestException:
        time.sleep(1)
        return fn(*args, **kwargs)


def _call_tool(name, args):
    try:
        if name == "get_nearby_places":
            places = _with_retry(tools.get_nearby_places, args["location"], args["interests"])
            if not places:
                return {
                    "status": "no_results",
                    "message": "No matching places nearby. Suggest a more central address or wider interests.",
                }
            return {"status": "ok", "places": [p.__dict__ for p in places]}

        if name == "order_walking_route":
            objs = [Place(**p) if isinstance(p, dict) else p for p in args["places"]]
            ordered = tools.order_walking_route(objs)
            return {"status": "ok", "places": [p.__dict__ for p in ordered]}

        return {"status": "error", "message": f"unknown tool {name}"}

    except ValueError as e:  # geocoder couldn't find the address
        log.warning("Tool %s rejected input: %s", name, e)
        return {"status": "error", "message": str(e)}
    except requests.exceptions.RequestException:
        log.exception("Tool %s: network/API failure after retry", name)
        return {
            "status": "error",
            "message": "The places service is having trouble. Apologise and suggest trying again shortly.",
        }
    except Exception:
        log.exception("Tool %s failed unexpectedly", name)
        return {"status": "error", "message": "Something went wrong building the tour. Apologise and suggest retrying."}


def run_agent(location, interests, user_note=""):
    ok, msg = tools.validate_request(location, interests)
    if not ok:
        log.info("Rejected by validate_request: %s", msg)
        return json.dumps({"intro": msg, "stops": []})

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Address: {location}\nInterests: {interests}\nExtra request: {user_note or 'none'}",
        },
    ]

    for round_num in range(MAX_ROUNDS):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
                temperature=0.3,
            )
        except OpenAIError:
            log.exception("LLM call failed (auth/quota/rate-limit/connection)")
            return json.dumps({
                "intro": "Sorry — the tour-building service is unavailable right now. Please try again later.",
                "stops": [],
            })
        msg_obj = resp.choices[0].message
        messages.append(msg_obj)

        if not msg_obj.tool_calls:
            log.info("Final answer after %d round(s).", round_num)
            return msg_obj.content

        for tc in msg_obj.tool_calls:
            args = json.loads(tc.function.arguments)
            log.info("TOOL CALL %s args=%s", tc.function.name, args)
            result = _call_tool(tc.function.name, args)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result)})

    log.warning("Hit MAX_ROUNDS without a final answer.")
    return json.dumps({"intro": "Sorry — I couldn't build a tour this time. Please try again.", "stops": []})
