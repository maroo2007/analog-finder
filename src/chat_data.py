"""Look up our results for the chatbot: targets, their Earth twins, Egypt.

Reads only the small committed JSON in web/public/data/ (built by
build_web_data.py), so the chatbot answers from exactly what the website
shows and never needs data/ or the internet. No Gemini code here: these are
plain functions, tested offline in tests/test_chat_data.py.

The functions under "Tools" are handed to Gemini, which calls them when a
question needs a number. Gemini reads each one's name, type hints and
docstring to decide when to call it, so keep those accurate. Every tool
returns plain dicts and lists (JSON), and an {"error": ...} dict with
suggestions instead of raising, so the model can recover from a misspelled
name.

Works with both data layouts: the Africa-only build, and the Americas build
that adds `continent`, `rank_continent` and `of_continent` to each twin.
"""

from __future__ import annotations

import difflib
import json
import re
from functools import lru_cache
from pathlib import Path

WEB_DATA = Path(__file__).resolve().parent.parent / "web" / "public" / "data"
FEATURE_LABELS = {"mean_slope": "slope (deg)", "slope_spread": "roughness (deg)",
                  "relief": "relief (m)", "albedo": "brightness (albedo 0-1)"}
MAX_TWINS = 25          # build_web_data.TOP_N: twins stored per target


# ------------------------------------------------------------ loading

@lru_cache(maxsize=None)
def _load(data_dir: str = str(WEB_DATA)) -> dict:
    root = Path(data_dir)
    targets = json.loads((root / "targets.json").read_text(encoding="utf-8"))
    egypt = json.loads((root / "egypt.json").read_text(encoding="utf-8"))
    by_id = {t["id"]: t for t in targets["targets"]}
    matches = {}
    for tid in by_id:
        path = root / "matches" / f"{tid}.json"
        matches[tid] = (json.loads(path.read_text(encoding="utf-8"))
                        if path.exists() else [])
    return {"targets": by_id, "egypt": {e["target"]: e for e in egypt},
            "matches": matches}


def data(data_dir: Path | str = WEB_DATA) -> dict:
    """All website data, read once and cached."""
    return _load(str(data_dir))


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def resolve(name: str, data_dir: Path | str = WEB_DATA) -> dict | None:
    """The target a name refers to: exact id or name first, ignoring case,
    spaces and punctuation, then a close spelling. None if nothing is close."""
    targets = data(data_dir)["targets"]
    key = _norm(name)
    for t in targets.values():
        if key in (_norm(t["id"]), _norm(t["name"])):
            return t
    # "Jezero crater" -> Jezero: a target name inside the question's name
    contained = [t for t in targets.values() if _norm(t["name"]) and
                 _norm(t["name"]) in key]
    if len(contained) == 1:
        return contained[0]
    names = {_norm(t["name"]): t for t in targets.values()}
    close = difflib.get_close_matches(key, list(names), n=1, cutoff=0.75)
    return names[close[0]] if close else None


def _suggest(name: str, data_dir) -> list[str]:
    targets = data(data_dir)["targets"].values()
    names = [t["name"] for t in targets]
    by_norm = {_norm(n): n for n in names}
    close = difflib.get_close_matches(_norm(name), list(by_norm), n=5, cutoff=0.4)
    return [by_norm[c] for c in close]


def maps_link(lat: float, lon: float) -> str:
    """Google Maps satellite view of a tile (same link as match_grid.maps_link,
    repeated here so the chatbot does not import the raster stack)."""
    return ("https://www.google.com/maps/@?api=1&map_action=map"
            f"&center={lat:.4f},{lon:.4f}&zoom=12&basemap=satellite")


def _twin(row: dict, n: int) -> dict:
    out = {"place": n, "lat": row["lat"], "lon": row["lon"],
           "country": row.get("country"), "score": row["score"],
           "rank": row["rank"], "out_of": row["of"],
           "features": row["features"], "closeness_pct": row["closeness"],
           "map": maps_link(row["lat"], row["lon"])}
    for key in ("continent", "rank_continent", "of_continent"):
        if key in row:
            out[key] = row[key]
    return out


def _summary(t: dict) -> dict:
    return {"name": t["name"], "id": t["id"], "world": t["world"],
            "lat": t["lat"], "lon": t["lon"], "best_score": t["best_score"]}


def coverage(data_dir: Path | str = WEB_DATA) -> dict:
    """What the Earth search covered, read from the data itself: how many
    Mars-possible tiles were ranked, and which continents (Africa only when
    the twins carry no continent field)."""
    rows = [r for m in data(data_dir)["matches"].values() for r in m]
    continents = sorted({r["continent"] for r in rows if r.get("continent")})
    return {"earth_tiles_ranked": max((r["of"] for r in rows), default=0),
            "continents": continents or ["Africa"]}


# ------------------------------------------------------------ tools

def list_targets(world: str = "") -> list[dict]:
    """List NASA's candidate sites that we matched against Earth.

    Args:
        world: "mars" for the 38 candidate human Exploration Zones, "moon" for
            the 9 Artemis III candidate regions near the lunar south pole, or
            empty for all of them.

    Returns each site's name, world, centre latitude and longitude, and the
    score of its best Earth twin (0 to 100; Moon scores are low and not
    comparable with Mars scores).
    """
    world = world.strip().lower()
    return [_summary(t) for t in data()["targets"].values()
            if not world or t["world"] == world]


def get_target(name: str) -> dict:
    """Details for one Mars or Moon site: its terrain, its 5 best Earth twins
    and its best twin inside Egypt.

    Args:
        name: the site's name, for example "Jezero", "Gale" or "Haworth".
            Close spellings are accepted.

    Returns the site's centre, the median of each feature over the site
    (slope, roughness, relief, and brightness for Mars), which features it is
    matched on, and the twins with score, rank among all ranked Earth tiles,
    country, features, per-feature closeness (100 = identical) and a map link.
    """
    t = resolve(name)
    if t is None:
        return {"error": f"No site called {name!r}.",
                "did_you_mean": _suggest(name, WEB_DATA)}
    d = data()
    out = {**_summary(t),
           "matched_on": [FEATURE_LABELS[f] for f in t["matched_on"]],
           "site_features_median": t["features"],
           "best_twins": [_twin(r, i) for i, r in
                          enumerate(d["matches"][t["id"]][:5], 1)]}
    if t.get("note"):
        out["note"] = t["note"]
    if t.get("area_km2"):
        out["area_km2"] = t["area_km2"]
    eg = d["egypt"].get(t["id"])
    if eg:
        out["best_in_egypt"] = {k: v for k, v in eg.items() if k != "target"}
        out["best_in_egypt"]["map"] = maps_link(eg["lat"], eg["lon"])
    return out


def get_twins(name: str, count: int = 10, country: str = "") -> dict:
    """The best Earth twins of one Mars or Moon site, best first. Twins are
    at least 25 km apart, so they are different places.

    Args:
        name: the site's name, for example "Jezero". Close spellings are
            accepted.
        count: how many twins to return, 1 to 25.
        country: optional. Only twins in this country, for example "Egypt"
            or "Chad". Only the site's stored top 25 are searched; for Egypt,
            get_target also gives the best Egyptian tile of all.
    """
    t = resolve(name)
    if t is None:
        return {"error": f"No site called {name!r}.",
                "did_you_mean": _suggest(name, WEB_DATA)}
    count = max(1, min(int(count), MAX_TWINS))
    rows = list(enumerate(data()["matches"][t["id"]], 1))
    if country.strip():
        want = _norm(country)
        rows = [(i, r) for i, r in rows if _norm(r.get("country") or "") == want]
    return {"site": t["name"], "world": t["world"],
            "twins": [_twin(r, i) for i, r in rows[:count]],
            "searched": f"the site's top {MAX_TWINS} twins"}


def twins_in_country(country: str) -> dict:
    """Which Mars and Moon sites have one of their top 25 Earth twins in a
    given country, with the best such twin for each site.

    Args:
        country: a country name as written in English, for example "Egypt",
            "Chad", "Morocco" or "Chile".
    """
    want = _norm(country)
    d = data()
    found, countries = [], set()
    for tid, rows in d["matches"].items():
        for i, r in enumerate(rows, 1):
            countries.add(r.get("country") or "")
            if _norm(r.get("country") or "") == want:
                found.append({"site": d["targets"][tid]["name"],
                              "world": d["targets"][tid]["world"],
                              **_twin(r, i)})
                break
    found.sort(key=lambda f: (f["world"] != "mars", -f["score"]))
    out = {"country": country, "sites": found}
    if not found:
        names = {_norm(c): c for c in countries if c}
        out["did_you_mean"] = [names[c] for c in difflib.get_close_matches(
            want, list(names), n=5, cutoff=0.5)]
    return out


TOOLS = [list_targets, get_target, get_twins, twins_in_country]
