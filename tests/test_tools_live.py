"""Live tests — hit the real Nominatim/Overpass APIs. Need internet.
Run with: pytest tests/test_tools_live.py -v
Skips (rather than fails) if the network/API is unreachable, since these
are free community servers without an SLA.
"""
import requests
import pytest

from models.contracts import INTERESTS
from tools import geocode, get_nearby_places, order_walking_route

SCENARIOS = [
    ("Allenby 29, Tel Aviv", ["architecture", "music", "art"]),
    ("Rothschild Blvd, Tel Aviv", ["history", "cafe"]),
    ("Jaffa Clock Tower", ["food", "museum", "nature"]),
]

# Tel Aviv-Jaffa bounding box, generous, to sanity-check geocoding results.
TLV_LAT_RANGE = (31.95, 32.15)
TLV_LON_RANGE = (34.70, 34.85)


def _skip_on_network_error(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except requests.exceptions.RequestException as e:
        pytest.skip(f"OSM service unreachable: {e}")


def test_geocode_known_address_is_in_tel_aviv():
    lat, lon = _skip_on_network_error(geocode, "Allenby 29, Tel Aviv")
    assert TLV_LAT_RANGE[0] <= lat <= TLV_LAT_RANGE[1]
    assert TLV_LON_RANGE[0] <= lon <= TLV_LON_RANGE[1]


def test_geocode_unknown_address_raises():
    with pytest.raises(ValueError):
        _skip_on_network_error(geocode, "zzzzzznotarealplace123456")


@pytest.mark.parametrize("address,interests", SCENARIOS)
def test_get_nearby_places_returns_valid_places(address, interests):
    places = _skip_on_network_error(get_nearby_places, address, interests)
    assert isinstance(places, list)
    for p in places:
        assert p.name
        assert p.category in INTERESTS
        assert -90 <= p.lat <= 90
        assert -180 <= p.lon <= 180


@pytest.mark.parametrize("address,interests", SCENARIOS)
def test_order_walking_route_preserves_the_same_places(address, interests):
    places = _skip_on_network_error(get_nearby_places, address, interests)
    if not places:
        pytest.skip("No places returned for this scenario right now (OSM coverage gap).")
    ordered = order_walking_route(places)
    assert sorted(p.name for p in ordered) == sorted(p.name for p in places)
