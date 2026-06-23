"""Fast, offline tests — no network calls. Run with: pytest tests/test_tools_unit.py"""
import pytest

from models.contracts import Place
from tools import (
    _build_overpass_query,
    _which_interest,
    order_walking_route,
    validate_request,
)


# --- validate_request ---------------------------------------------------

def test_validate_request_rejects_empty_address():
    ok, msg = validate_request("", ["cafe"])
    assert not ok
    assert "address" in msg.lower()


def test_validate_request_rejects_blank_address():
    ok, msg = validate_request("   ", ["cafe"])
    assert not ok


def test_validate_request_rejects_no_interests():
    ok, msg = validate_request("Allenby 29, Tel Aviv", [])
    assert not ok
    assert "interest" in msg.lower()


def test_validate_request_rejects_unknown_interest():
    ok, msg = validate_request("Allenby 29, Tel Aviv", ["bogus"])
    assert not ok
    assert "bogus" in msg


def test_validate_request_accepts_valid_input():
    ok, msg = validate_request("Allenby 29, Tel Aviv", ["cafe", "music"])
    assert ok
    assert msg == ""


# --- order_walking_route (pure math, no network) ------------------------

def test_order_walking_route_empty_list():
    assert order_walking_route([]) == []


def test_order_walking_route_single_place():
    p = Place("Solo", "cafe", 32.0, 34.0)
    assert order_walking_route([p]) == [p]


def test_order_walking_route_picks_nearest_next():
    # far, near, mid relative to the first place picked as the start.
    start = Place("Start", "cafe", 32.000, 34.000)
    near = Place("Near", "cafe", 32.001, 34.000)
    mid = Place("Mid", "cafe", 32.003, 34.000)
    far = Place("Far", "cafe", 32.010, 34.000)

    ordered = order_walking_route([start, far, near, mid])

    assert [p.name for p in ordered] == ["Start", "Near", "Mid", "Far"]


def test_order_walking_route_with_explicit_start():
    a = Place("A", "cafe", 32.001, 34.000)
    b = Place("B", "cafe", 32.010, 34.000)
    ordered = order_walking_route([b, a], start_lat=32.000, start_lon=34.000)
    assert [p.name for p in ordered] == ["A", "B"]


def test_order_walking_route_no_duplicates_or_drops():
    places = [
        Place("A", "cafe", 32.001, 34.000),
        Place("B", "cafe", 32.002, 34.001),
        Place("C", "cafe", 32.003, 34.002),
    ]
    ordered = order_walking_route(places)
    assert sorted(p.name for p in ordered) == ["A", "B", "C"]


# --- helpers --------------------------------------------------------------

def test_which_interest_matches_known_tag():
    assert _which_interest({"amenity": "cafe"}, ["cafe", "music"]) == "cafe"


def test_which_interest_falls_back_to_first_interest():
    assert _which_interest({"shop": "bakery"}, ["cafe", "music"]) == "cafe"


def test_which_interest_with_no_interests_defaults_to_history():
    assert _which_interest({"shop": "bakery"}, []) == "history"


def test_build_overpass_query_includes_each_interest_filter():
    query = _build_overpass_query(32.07, 34.78, ["cafe", "museum"], 800)
    assert 'around:800,32.07,34.78' in query
    assert '["amenity"="cafe"]' in query
    assert '["tourism"="museum"]' in query
