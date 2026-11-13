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
import run_diviner as dv  # noqa: E402
import match_grid as m  # noqa: E402
import run_moon_targets as rm  # noqa: E402
import terrain as t  # noqa: E402

WEB = ROOT / "web" / "public" / "data"
MARS_EZ = ROOT / "src" / "targets" / "mars_human_ez.json"
MOON = ROOT / "src" / "targets" / "moon_artemis.json"
MOON_KM_PER_DEG = math.pi * t.MOON_RADIUS_M / 180 / 1000


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
    # rank is the position among all `of` ranked tiles: the best twin is the
    # closest tile of all, and later twins rank lower but never out of order
    ranks = [r["rank"] for r in rows]
    assert ranks[0] == 1 and ranks == sorted(ranks) and len(set(ranks)) == len(ranks)
    assert len({r["of"] for r in rows}) == 1 and rows[0]["of"] > 100_000
    # rank_continent: the same order counted within the tile's continent, so
    # it is never worse than the overall rank and rises in order per continent
    for cont in {r["continent"] for r in rows}:
        mine = [r for r in rows if r["continent"] == cont]
        rc = [r["rank_continent"] for r in mine]
        assert rc == sorted(rc) and len(set(rc)) == len(rc)
        assert all(r["rank_continent"] <= r["rank"] for r in mine)
        assert all(r["of_continent"] <= r["of"] for r in mine)
    best = rows[0]
    assert best["rank_continent"] == 1


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


def test_jezero_best_twin_in_africa_is_in_egypts_eastern_desert():
    """The headline: Africa's closest tile to Jezero is in Egypt's Eastern
    Desert. Counted within Africa, so it holds as continents are added."""
    best = next(e for e in _json(WEB / "egypt.json") if e["target"] == "jezero")
    assert best["rank_continent"] == 1     # Egypt's best is Africa's best
    assert m.haversine_km(best["lat"], best["lon"], 25.13, 34.54) < 15


def test_egypt_rows_rank_within_africa():
    for e in _json(WEB / "egypt.json"):
        assert 1 <= e["rank_continent"] <= e["rank"] <= e["of"]
        assert e["of_continent"] <= e["of"]


# ------------------------------------------------------------------ the Moon

def test_moon_file_is_labelled_with_sources():
    doc = _json(MOON)
    assert "Artemis III" in doc["title"] and "Artemis IV" in doc["caveat"]
    assert all(str(v).count("https://") >= 1 for v in doc["sources"].values())
    assert len(doc["regions"]) == 9
    assert len({r["id"] for r in doc["regions"]}) == 9


@pytest.mark.parametrize("region", _json(MOON)["regions"], ids=lambda r: r["id"])
def test_moon_region_agrees_with_nasa_table(region):
    """Centre within 5 km of the latitude in NASA's LEMS-A3 table (we agreed
    to flag anything further), area within 1%, centre inside its outline."""
    from shapely.geometry import Point, Polygon
    assert region["lat"] < t.MOON_SOUTH_LIMIT
    dlat_km = abs(region["lat"] - region["nasa_centre_lat"]) * MOON_KM_PER_DEG
    assert dlat_km < 5, f"{dlat_km:.1f} km from NASA's centre latitude"
    assert region["area_km2"] == pytest.approx(region["nasa_area_km2"], rel=0.01)
    poly = Polygon([t.moon_xy(lat, lon) for lon, lat in region["outline"]])
    assert poly.contains(Point(t.moon_xy(region["lat"], region["lon"])))


def test_moon_xy_matches_proj():
    """The hand-written projection must equal the DEM's own (PROJ)."""
    from pyproj import Transformer
    proj = Transformer.from_crs(
        f"+proj=longlat +R={t.MOON_RADIUS_M} +no_defs",
        f"+proj=stere +lat_0=-90 +lat_ts=-90 +lon_0=0 +R={t.MOON_RADIUS_M} +units=m",
        always_xy=True)
    for lat, lon in [(-89.67, 129.78), (-83.6, -68.7), (-88.2, -64.6), (-80, 180)]:
        assert t.moon_xy(lat, lon) == pytest.approx(proj.transform(lon, lat), abs=0.01)


def test_moon_boxes_follow_the_rule_and_avoid_the_pole():
    """Extent + 15 km a side, at least 120 px, whole tiles, never the pole."""
    boxes = {r["id"]: rm.box_px(r) for r in rm.load_regions()}
    assert all(px >= rm.MIN_BOX_PX and px % t.TILE_PX == 0 for px in boxes.values())
    assert boxes["mons_mouton_plateau"] == 240      # 67 km region
    assert boxes["haworth"] == 140                  # 30 km region
    for r in rm.load_regions():
        assert not rm.box_reaches_pole(r, boxes[r["id"]]), r["id"]


def test_moon_targets_in_web_data_are_terrain_only():
    moon = [x for x in _targets() if x["world"] == "moon"]
    assert len(moon) == 9
    for x in moon:
        assert x["matched_on"] == t.FEATURES
        assert "albedo" in x["note"]
        rows = _json(WEB / "matches" / f"{x['id']}.json")
        assert all(set(r["closeness"]) == set(t.FEATURES) for r in rows)
        assert (WEB / "shade" / "moon" / f"{x['id']}.png").exists()


# ------------------------------------------------------------------ Diviner

def test_diviner_projection_matches_moon_xy():
    lat = np.array([-84.0, -86.5, -89.9])
    lon = np.array([-170.0, 12.5, 128.0])
    x, y = dv.stereo_xy(lat, lon)
    for i in range(3):
        ex, ey = t.moon_xy(lat[i], lon[i])
        assert x[i] == pytest.approx(ex) and y[i] == pytest.approx(ey)


def test_diviner_region_test_finds_its_own_centre():
    regions = rm.load_regions()
    for r in regions:
        assert dv.inside(r, np.array([r["lat"]]), np.array([r["lon"]]))[0], r["id"]
    far = np.array([-80.5]), np.array([180.0])
    assert not any(dv.inside(r, *far)[0] for r in regions)


def test_moon_targets_carry_diviner_context():
    """Diviner is context on every Moon card, never a matching feature."""
    moon = [x for x in _targets() if x["world"] == "moon"]
    for x in moon:
        d = x["diviner"]
        assert x["matched_on"] == t.FEATURES          # still terrain only
        assert "doi:10.1126/science.1187726" in d["source"]
        assert all(f.startswith("https://pds-geosciences.wustl.edu/") for f in d["files"])
        assert "not permanent shadow" in d["note"]
        for key in ("annual_max_surface", "annual_mean_2cm"):
            k, c = d[key]["k"], d[key]["c"]
            assert 20 < k["lowest"] <= k["mean"] <= k["highest"] < 420, x["id"]
            assert c["mean"] == pytest.approx(k["mean"] - 273.15, abs=0.11)
        # an annual mean can never beat the annual maximum
        assert d["annual_mean_2cm"]["k"]["mean"] < d["annual_max_surface"]["k"]["mean"]
        shares = [d["ice_stable_surface_share"], d["ice_stable_within_2_9m_share"]]
        assert 0 <= shares[0] <= shares[1] <= 1
        assert 0 <= d["cold_trap_share"] <= 1
        # the triangles found cover the region NASA describes
        assert 0.8 < d["area_km2"] / x["area_km2"] < 1.25, x["id"]


# ------------------------------------------------------------ shaded relief

def test_every_twin_has_its_shaded_relief():
    """render_shades.py --twins: one WebP per twin (numbered by its place in
    matches/<id>.json), per Egypt row and per target. A rebuild of the web
    data that is not followed by a render fails here."""
    egypt = {e["target"] for e in _json(WEB / "egypt.json")}
    shade = WEB / "shade"
    for x in _targets():
        tid = x["id"]
        rows = _json(WEB / "matches" / f"{tid}.json")
        names = [f"{tid}_{n}.webp" for n in range(1, len(rows) + 1)]
        names += [f"{tid}_egypt.webp"] if tid in egypt else []
        missing = [n for n in names if not (shade / "earth" / n).exists()]
        assert not missing, missing
        assert (shade / x["world"] / f"{tid}.webp").exists(), tid
    assert not list(shade.rglob("*.part"))              # no half-written file
