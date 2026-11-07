"""Tests for the parts of the web data that can break quietly.

A wrong score formula, a spacing rule that lets twins crowd together, or a
target with a swapped latitude and longitude would all still produce valid
JSON, and the website would show them without complaint. These tests catch
that. They need no internet and run in a second:

    pytest tests/test_web_data.py
"""

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import build_web_data as w  # noqa: E402
import match_grid as m  # noqa: E402

WEB = ROOT / "web" / "public" / "data"
MARS_EZ = ROOT / "src" / "targets" / "mars_human_ez.json"


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


# ------------------------------------------------------- score and closeness

def test_score_formula():
    """Score = 100 * exp(-distance / 0.4): 100 for a perfect match, 1/e of
    that at 0.4 standard deviations, always falling as distance grows."""
    assert w.score(0.0) == 100.0
    assert w.score(w.SCALE) == pytest.approx(100 / math.e, abs=0.05)
    s = w.score(np.linspace(0, 5, 51))
    assert (np.diff(s) <= 0).all()
    assert s.min() >= 0


def test_closeness_formula():
    """100 when a feature matches exactly, 50 at one standard deviation, 0 at
    two or more, the same on either side."""
    c = w.closeness(np.array([0.0, 1.0, -1.0, 2.0, -3.0]))
    assert c.tolist() == [100.0, 50.0, 50.0, 0.0, 0.0]


# ------------------------------------------------------------ 25 km spacing

def test_both_tools_use_the_same_spacing_rule():
    """match_grid (the command line lists) and build_web_data (the website)
    must give the same twins, so there is only one top_spread."""
    assert w.top_spread is m.top_spread
    assert m.SPACING_KM == 25.0


def test_haversine_known_distances():
    assert m.haversine_km(0, 0, 0, 0) == pytest.approx(0)
    # one degree of latitude is about 111.2 km everywhere
    assert m.haversine_km(10, 30, 11, 30) == pytest.approx(111.19, abs=0.05)
    # 0.25 degree of longitude at 35 S is only 22.8 km: the case the old
    # degree-box rule got wrong
    assert m.haversine_km(-35, 20, -35, 20.25) == pytest.approx(22.78, abs=0.05)


def test_top_spread_skips_close_tiles():
    """At 35 S, a tile 0.25 degree east is 22.8 km away and must be skipped;
    one 0.30 degree east is 27.3 km away and must be kept."""
    ranked = pd.DataFrame({"lat": [-35.0, -35.0, -35.0, -34.0],
                           "lon": [20.0, 20.25, 20.30, 20.0]})
    top = m.top_spread(ranked, 10)
    assert list(zip(top.lat, top.lon)) == [(-35.0, 20.0), (-35.0, 20.30),
                                           (-34.0, 20.0)]
    assert top["idx"].tolist() == [0, 2, 3]


def test_top_spread_keeps_diagonal_neighbour_25_km_away():
    """The old 0.25 degree box wrongly blocked this tile: it is under 0.25
    degree away in both directions but about 26 km away on the ground."""
    ranked = pd.DataFrame({"lat": [0.0, 0.17], "lon": [30.0, 30.17]})
    assert m.haversine_km(0, 30, 0.17, 30.17) > 25
    assert len(m.top_spread(ranked, 10)) == 2


def test_top_spread_stops_at_n():
    ranked = pd.DataFrame({"lat": np.arange(10.0), "lon": np.zeros(10)})
    assert len(m.top_spread(ranked, 4)) == 4


def _targets():
    return _json(WEB / "targets.json")["targets"]


@pytest.mark.parametrize("tid", [t["id"] for t in _targets()])
def test_published_twins_are_25_km_apart(tid):
    rows = _json(WEB / "matches" / f"{tid}.json")
    assert 1 <= len(rows) <= w.TOP_N
    lat = np.array([r["lat"] for r in rows])
    lon = np.array([r["lon"] for r in rows])
    d = m.haversine_km(lat[:, None], lon[:, None], lat[None, :], lon[None, :])
    np.fill_diagonal(d, np.inf)
    assert d.min() >= m.SPACING_KM, f"closest pair {d.min():.1f} km"
    scores = [r["score"] for r in rows]
    assert scores == sorted(scores, reverse=True)
    assert all(0 <= s <= 100 for s in scores)


# ------------------------------------------------------------- the targets

def test_mars_zone_list():
    zones = _json(MARS_EZ)
    assert len(zones) == 38
    assert len({z["id"] for z in zones}) == 38
    for z in zones:
        west, south, east, north = z["bbox"]
        assert west < z["lon"] < east and south < z["lat"] < north, z["id"]


def test_targets_json_has_38_mars_zones_with_valid_coordinates():
    targets = _targets()
    ids = [t["id"] for t in targets]
    assert len(ids) == len(set(ids)), "duplicate target ids"
    mars = [t for t in targets if t["world"] == "mars"]
    assert len(mars) == 38
    assert {t["id"] for t in mars} == {z["id"] for z in _json(MARS_EZ)}
    for t in targets:
        assert -90 <= t["lat"] <= 90 and -180 <= t["lon"] <= 180, t["id"]
        assert (WEB / "matches" / f"{t['id']}.json").exists(), t["id"]


def test_gale_and_jezero_centres():
    """Spot-check two zones against their known positions, which would catch
    swapped or sign-flipped coordinates."""
    by_id = {t["id"]: t for t in _targets()}
    assert by_id["gale"]["lat"] == pytest.approx(-5.4, abs=1.0)
    assert by_id["gale"]["lon"] == pytest.approx(137.8, abs=1.0)
    assert by_id["jezero"]["lat"] == pytest.approx(18.4, abs=1.0)
    assert by_id["jezero"]["lon"] == pytest.approx(77.5, abs=1.0)


def test_jezero_best_twin_is_in_egypts_eastern_desert():
    best = _json(WEB / "matches" / "jezero.json")[0]
    assert best["country"] == "Egypt"
    assert m.haversine_km(best["lat"], best["lon"], 25.13, 34.54) < 15
