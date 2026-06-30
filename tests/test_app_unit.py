"""Fast, offline tests for the app's pure logic — no Streamlit, no network.

Run with:  pytest tests/test_app_unit.py
These cover the functions in app_logic.py that drive the UI's behaviour, so
the screen logic (duration sizing, parsing the agent's reply, validating
coordinates) is checked without rendering any widgets.
"""
import json

import pytest

from app_logic import compose_note, fake_agent, parse_tour, valid_coord
from models.contracts import minutes_to_stops


# --- minutes_to_stops (shared with the agent) ---------------------------

@pytest.mark.parametrize("minutes,expected", [
    (15, 4), (30, 4), (60, 4), (90, 5), (120, 6), (180, 6),
])
def test_minutes_to_stops_mapping(minutes, expected):
    assert minutes_to_stops(minutes) == expected


def test_minutes_to_stops_is_clamped_4_to_6():
    assert minutes_to_stops(1) == 4        # never fewer than 4
    assert minutes_to_stops(10_000) == 6   # never more than 6


# --- compose_note -------------------------------------------------------

def test_compose_note_includes_duration():
    note = compose_note(60)
    assert "60 minutes" in note


def test_compose_note_combines_duration_and_refine_text():
    note = compose_note(90, "more cafes")
    assert "90 minutes" in note
    assert "more cafes" in note


def test_compose_note_empty_when_nothing_given():
    assert compose_note(None, "") == ""


# --- parse_tour ---------------------------------------------------------

VALID = {"intro": "hi", "stops": [
    {"name": "A", "category": "art", "lat": 1.0, "lon": 2.0, "narration": "n"}]}


def test_parse_tour_plain_json_string():
    assert parse_tour(json.dumps(VALID))["stops"][0]["name"] == "A"


def test_parse_tour_strips_json_fences():
    fenced = "```json\n" + json.dumps(VALID) + "\n```"
    assert parse_tour(fenced)["intro"] == "hi"


def test_parse_tour_extracts_json_from_surrounding_prose():
    messy = "Here is your tour:\n" + json.dumps(VALID) + "\nEnjoy!"
    assert parse_tour(messy)["intro"] == "hi"


def test_parse_tour_dict_passthrough():
    assert parse_tour(VALID) is VALID


def test_parse_tour_garbage_returns_none():
    assert parse_tour("not json at all") is None


def test_parse_tour_non_string_returns_none():
    assert parse_tour(12345) is None


# --- valid_coord (map guard) -------------------------------------------

def test_valid_coord_accepts_real_point():
    assert valid_coord({"lat": 32.07, "lon": 34.78}) is True


def test_valid_coord_accepts_numeric_strings():
    assert valid_coord({"lat": "32.07", "lon": "34.78"}) is True


def test_valid_coord_rejects_missing_keys():
    assert valid_coord({"name": "no coords"}) is False


def test_valid_coord_rejects_non_numeric():
    assert valid_coord({"lat": "north", "lon": 34.0}) is False


def test_valid_coord_rejects_out_of_range():
    assert valid_coord({"lat": 999, "lon": 34.0}) is False     # impossible latitude
    assert valid_coord({"lat": 32.0, "lon": 500}) is False     # impossible longitude


# --- fake_agent (demo mode) --------------------------------------------

def test_fake_agent_returns_only_chosen_interests():
    tour = fake_agent("Allenby 29", ["architecture", "cafe"])
    assert tour["stops"]
    assert all(s["category"] in ("architecture", "cafe") for s in tour["stops"])


def test_fake_agent_falls_back_when_no_match():
    # 'art' has no sample stop -> falls back to a default walk (floor of 4).
    assert len(fake_agent("X", ["art"])["stops"]) == 4


def test_fake_agent_respects_duration_in_note():
    allcats = ["architecture", "cafe", "music", "museum", "food", "nature", "history"]
    short = fake_agent("X", allcats, compose_note(30))   # -> 4 stops
    long = fake_agent("X", allcats, compose_note(120))   # -> 6 stops
    assert len(short["stops"]) == 4
    assert len(long["stops"]) == 6


def test_fake_agent_output_matches_contract_shape():
    tour = fake_agent("X", ["cafe"])
    assert set(tour) == {"intro", "stops"}
    for stop in tour["stops"]:
        assert {"name", "category", "lat", "lon", "narration"} <= set(stop)
