"""Tests for the chatbot's lookups (src/chat_data.py).

The chatbot's numbers are only as good as these lookups, so check they find
the right site from loose spellings, return the website's own numbers, and
fail with suggestions rather than an exception. Offline, no Gemini key:

    pytest tests/test_chat_data.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import chat_data as c  # noqa: E402

WEB = ROOT / "web" / "public" / "data"


def test_list_targets_counts():
    assert len(c.list_targets("mars")) == 38
    assert len(c.list_targets("moon")) == 9
    assert len(c.list_targets()) == 47


def test_resolve_loose_names():
    assert c.resolve("jezero")["id"] == "jezero"
    assert c.resolve("Jezero Crater")["id"] == "jezero"
    assert c.resolve("Jezro")["id"] == "jezero"              # typo
    assert c.resolve("de gerlache rim 2")["world"] == "moon"
    # exact names win over names they contain
    assert c.resolve("Arcadia")["name"] == "Arcadia"
    assert c.resolve("Arcadia Planitia")["name"] == "Arcadia Planitia"
    assert c.resolve("Olympus Mons") is None


def test_get_target_matches_website_data():
    tgt = c.get_target("Gale")
    raw = json.loads((WEB / "matches" / "gale.json").read_text(encoding="utf-8"))
    assert tgt["best_twins"][0]["score"] == raw[0]["score"]
    assert tgt["best_twins"][0]["lat"] == raw[0]["lat"]
    assert len(tgt["best_twins"]) == 5
    assert "google.com/maps" in tgt["best_twins"][0]["map"]
    assert tgt["best_in_egypt"]["lat"]


def test_moon_target_says_terrain_only():
    tgt = c.get_target("Haworth")
    assert "brightness (albedo 0-1)" not in tgt["matched_on"]
    assert "terrain only" in tgt["note"]


def test_unknown_name_suggests():
    out = c.get_target("Jezzero basin")
    assert "error" in out and "Jezero" in out["did_you_mean"]
    out = c.get_twins("Nothing Like It")
    assert "error" in out and isinstance(out["did_you_mean"], list)


def test_get_twins_count_and_country():
    assert len(c.get_twins("Jezero", count=100)["twins"]) <= c.MAX_TWINS
    assert len(c.get_twins("Jezero", count=0)["twins"]) == 1
    for twin in c.get_twins("Jezero", count=25, country="egypt")["twins"]:
        assert twin["country"] == "Egypt"


def test_twins_in_country():
    out = c.twins_in_country("Egypt")
    assert out["sites"], "Egypt holds twins of several Mars sites"
    assert all(s["country"] == "Egypt" for s in out["sites"])
    assert c.twins_in_country("Atlantis")["sites"] == []


def test_coverage_reads_the_data():
    cov = c.coverage()
    assert cov["earth_tiles_ranked"] > 100000
    assert "Africa" in cov["continents"]


def test_tools_return_json():
    for tool, args in [(c.list_targets, ("",)), (c.get_target, ("Gale",)),
                       (c.get_twins, ("Gale", 3, "")),
                       (c.twins_in_country, ("Chad",))]:
        json.dumps(tool(*args))
