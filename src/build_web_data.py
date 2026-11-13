"""Build the small JSON files the web interface reads, from the V1 matching.

Inputs (all gitignored, built by earlier steps):
  data/processed/mars_ez_v1.parquet      V1 report cards for NASA's candidate
                                         human Exploration Zones on Mars
  data/processed/moon_artemis_v1.parquet terrain report cards for the nine
                                         Artemis III regions (run_moon_targets)
  data/processed/earth_grid/             the Earth grid areas built so far
                                         (EARTH_AREAS: Africa, the Americas)

Outputs (committed, small): web/public/data/
  targets.json            every Mars zone and Moon region ("world": "mars"
                          or "moon"), its median features and centre
  matches/<id>.json       top Earth twins for that target, at least 25 km apart,
                          each with its raw score, its rank among all `of`
                          ranked Mars-possible tiles, its rank_continent among
                          the of_continent tiles of its own continent, and
                          per-feature closeness
  egypt.json              best Egyptian tile for every target
  likeness*.png + .json   "how Mars-like" map per continent (Mars only):
                          likeness.png (Africa), likeness_americas.png;
                          likeness.json lists them with their bounds

Method, same as V1 in match_grid.py: features are standardized, a tile's
distance to a target is its mean distance to the target's 10 nearest tiles.
For each world, one scaler is fitted on all its target tiles and all
Mars-possible Africa tiles together, so scores are comparable across that
world's targets. Mars uses the V1 features (terrain and albedo); the Moon
uses terrain only (MOON_FEATURES). A Moon box holds 36 to 144 tiles against
about 400 for a Mars zone, so the 10 nearest are a larger share of it and a
Moon score describes more of the region at once.

    python src/build_web_data.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

import config
import earth_grid as g
import run_moon_targets
import terrain as t
from match_grid import top_spread
from run_thermal import FEATURES_V1

# The Moon is matched on terrain only: there is no Moon albedo source yet.
MOON_FEATURES = t.FEATURES

# Earth grid areas (earth_grid.AREAS) and the continent each one is.
EARTH_AREAS = {"africa": "Africa", "americas": "Americas"}
# Likeness map extents, [west, east, south, north]. Africa's is unchanged.
LIKENESS_BOUNDS = {"africa": (-18.0, 52.0, -35.0, 38.0),
                   "americas": (-125.0, -34.0, -56.5, 50.0)}
MOON_NOTE = ("Matched on terrain only (slope, roughness, relief): there is "
             "no Moon albedo source yet.")

OUT = config.ROOT / "web" / "public" / "data"
NEIGHBOURS = 10
TOP_N = 25          # twins per zone, at least match_grid.SPACING_KM apart
# Score = 100 * exp(-distance / SCALE), distance in standard deviations.
# With 0.4, a tile on average 0.4 standard deviations from the zone scores
# 37, the median dry Africa tile scores 1 to 5, and the best twins of easy
# zones (flat plains) score 90+ while hard ones (steep canyons) stay near 50.
# It only changes the labels, never the ranking.
SCALE = 0.4
FEATURE_LABELS = {"mean_slope": "Slope", "slope_spread": "Roughness",
                  "relief": "Relief", "albedo": "Brightness"}
UNITS = {"mean_slope": "°", "slope_spread": "°", "relief": "m", "albedo": ""}


def score(distance):
    return np.round(100 * np.exp(-np.asarray(distance) / SCALE), 1)


def closeness(delta_z):
    """100 when a feature matches exactly, 0 at two standard deviations."""
    return np.round(np.clip(1 - np.abs(delta_z) / 2, 0, 1) * 100, 0)


def match_world(targets: list[dict], cards: pd.DataFrame, earth: pd.DataFrame,
                features: list[str], world: str):
    """Rank the Earth tiles for every target of one world.

    One scaler is fitted on that world's target tiles and the Earth tiles
    together, on the features that world has, so scores are comparable
    across its targets. Writes matches/<id>.json and returns the targets.json
    entries, the egypt.json rows and every Earth tile's best score.
    """
    cards = cards.dropna(subset=features)
    earth = earth.dropna(subset=features).reset_index(drop=True)
    of_continent = earth["continent"].value_counts()
    scaler = StandardScaler().fit(pd.concat([earth[features], cards[features]]))
    ez = scaler.transform(earth[features])

    (OUT / "matches").mkdir(parents=True, exist_ok=True)
    best_any = np.full(len(earth), np.inf)
    egypt_rows, out_targets = [], []
    for tgt in targets:
        site = cards[cards["site"] == tgt["name"]]
        sz = scaler.transform(site[features])
        nn = NearestNeighbors(n_neighbors=NEIGHBOURS).fit(sz)
        dist, idx = nn.kneighbors(ez)
        d = dist.mean(axis=1)
        best_any = np.minimum(best_any, d)
        near = sz[idx].mean(axis=1)            # mean of the 10 nearest target tiles
        delta = ez - near

        ranked = earth.assign(distance=d).sort_values("distance")
        # rank: position in that same order (1 = closest of all `of` tiles),
        # so the site can say "closest of 130,060" when a raw score looks low
        rank = np.empty(len(earth), dtype=int)
        rank[ranked.index.to_numpy()] = np.arange(1, len(earth) + 1)
        # rank_continent: the same order, counted within the tile's own
        # continent, so "closest in Africa" stays true as continents are added
        rank_c = np.empty(len(earth), dtype=int)
        within = ranked.groupby("continent", sort=False).cumcount() + 1
        rank_c[within.index.to_numpy()] = within.to_numpy()
        top = top_spread(ranked, TOP_N)
        rows = []
        for r in top.itertuples():
            i = r.idx
            rows.append({
                "lat": round(r.lat, 4), "lon": round(r.lon, 4),
                "country": r.country, "continent": r.continent,
                "score": float(score(r.distance)),
                "rank": int(rank[i]), "of": len(earth),
                "rank_continent": int(rank_c[i]),
                "of_continent": int(of_continent[r.continent]),
                "features": {f: round(float(getattr(r, f)), 3)
                             for f in features},
                "closeness": {f: float(c) for f, c in
                              zip(features, closeness(delta[i]))},
            })
        (OUT / "matches" / f"{tgt['id']}.json").write_text(json.dumps(rows))

        eg = ranked[ranked["country"] == "Egypt"].head(1)
        if len(eg):
            r = eg.iloc[0]
            egypt_rows.append({"target": tgt["id"], "lat": round(r.lat, 4),
                               "lon": round(r.lon, 4),
                               "score": float(score(r.distance)),
                               "rank": int(rank[eg.index[0]]), "of": len(earth),
                               "rank_continent": int(rank_c[eg.index[0]]),
                               "of_continent": int(of_continent["Africa"])})

        med = site[features].median()
        out_targets.append({**tgt, "world": world, "matched_on": features,
                            "features": {f: round(float(med[f]), 3)
                                         for f in features},
                            "best_score": rows[0]["score"] if rows else None})
        print(f"{world:4s} {tgt['name']:32s} best {rows[0]['score']:5.1f} "
              f"{rows[0]['country']}", flush=True)
    return out_targets, egypt_rows, earth.assign(score=score(best_any))


def moon_targets() -> list[dict]:
    """The Artemis regions, with the keys the website needs."""
    keep = ("id", "name", "lat", "lon", "bbox", "code", "area_km2", "outline")
    return [{**{k: r[k] for k in keep}, "note": MOON_NOTE}
            for r in run_moon_targets.load_regions()]


def main() -> int:
    mars = pd.read_parquet(config.PROCESSED / "mars_ez_v1.parquet")
    moon = pd.read_parquet(config.PROCESSED / "moon_artemis_v1.parquet")
    mars_targets = json.loads((Path(__file__).parent / "targets" /
                               "mars_human_ez.json").read_text(encoding="utf-8"))
    earth = load_earth()

    mars_out, mars_egypt, mars_scored = match_world(
        mars_targets, mars, earth, FEATURES_V1, "mars")
    moon_out, moon_egypt, _ = match_world(
        moon_targets(), moon, earth, MOON_FEATURES, "moon")

    (OUT / "targets.json").write_text(json.dumps(
        {"features": [{"key": f, "label": FEATURE_LABELS[f], "unit": UNITS[f]}
                      for f in FEATURES_V1],
         "targets": mars_out + moon_out}, indent=1))
    (OUT / "egypt.json").write_text(json.dumps(mars_egypt + moon_egypt, indent=1))
    # The maps are Mars likeness only: one image per continent.
    maps = [write_likeness(mars_scored[mars_scored["continent"] == name], area,
                           LIKENESS_BOUNDS[area])
            for area, name in EARTH_AREAS.items() if area in LIKENESS_BOUNDS
            and (mars_scored["continent"] == name).any()]
    (OUT / "likeness.json").write_text(json.dumps(
        {"bounds": maps[0]["bounds"], "maps": maps}))   # bounds: Africa, as before
    return 0


def load_earth() -> pd.DataFrame:
    """Mars-possible tiles of every Earth grid area built so far, tagged with
    their continent. The areas do not overlap."""
    parts = []
    for area, name in EARTH_AREAS.items():
        if not (g.GRID_DIR / f"{area}_surface.parquet").exists():
            print(f"no {area} grid yet, skipped", flush=True)
            continue
        grid = g.load(area)
        parts.append(grid[grid["mars_possible"]].assign(continent=name))
    earth = pd.concat(parts, ignore_index=True)
    print("Earth tiles: " + ", ".join(f"{c} {n:,}" for c, n in
                                      earth["continent"].value_counts().items()))
    return earth


def write_likeness(earth: pd.DataFrame, area: str, box) -> dict:
    """A transparent PNG over one area: brighter = more Mars-like."""
    from PIL import Image
    step = 1 / 12
    west, east, south, north = box
    w, h = round((east - west) / step), round((north - south) / step)
    img = np.zeros((h, w, 4), dtype=np.uint8)
    col = ((earth["lon"] - west) / step).astype(int).clip(0, w - 1)
    row = ((north - earth["lat"]) / step).astype(int).clip(0, h - 1)
    s = (earth["score"] / 100).clip(0, 1).to_numpy()
    # dark red -> orange -> pale yellow, alpha grows with the score
    ramp = np.array([[90, 20, 10], [200, 70, 30], [245, 160, 60],
                     [255, 235, 170]], dtype=float)
    pos = s * (len(ramp) - 1)
    lo = np.floor(pos).astype(int).clip(0, len(ramp) - 2)
    frac = (pos - lo)[:, None]
    rgb = ramp[lo] * (1 - frac) + ramp[lo + 1] * frac
    img[row, col, :3] = rgb.astype(np.uint8)
    img[row, col, 3] = (60 + 195 * s).astype(np.uint8)
    name = "likeness.png" if area == "africa" else f"likeness_{area}.png"
    Image.fromarray(img).save(OUT / name, optimize=True)
    return {"area": area, "image": name, "bounds": [[south, west], [north, east]]}


if __name__ == "__main__":
    sys.exit(main())
