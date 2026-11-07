"""Build the small JSON files the web interface reads, from the V1 matching.

Inputs (all gitignored, built by earlier steps):
  data/processed/mars_ez_v1.parquet   V1 report cards for NASA's candidate
                                      human Exploration Zones on Mars
  data/processed/earth_grid/          the Africa grid (earth_grid.load)

Outputs (committed, small): web/public/data/
  targets.json            every Mars zone, its median features and centre
  matches/<id>.json       top Earth twins for that zone, at least 25 km apart
  egypt.json              best Egyptian tile for every zone
  likeness.png + .json    Africa's "how Mars-like" map and its bounds

Method, same as V1 in match_grid.py: features are standardized, a tile's
distance to a zone is its mean distance to the zone's 10 nearest Mars tiles.
One scaler is fitted on all Mars zone tiles and all Mars-possible Africa
tiles together, so scores are comparable across zones.

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
from match_grid import top_spread
from run_thermal import FEATURES_V1

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


def main() -> int:
    mars = pd.read_parquet(config.PROCESSED / "mars_ez_v1.parquet")
    mars = mars.dropna(subset=FEATURES_V1)
    targets = json.loads((Path(__file__).parent / "targets" /
                          "mars_human_ez.json").read_text(encoding="utf-8"))
    grid = g.load("africa")
    earth = grid[grid["mars_possible"]].dropna(subset=FEATURES_V1)
    earth = earth.reset_index(drop=True)

    scaler = StandardScaler().fit(pd.concat([earth[FEATURES_V1],
                                             mars[FEATURES_V1]]))
    ez = scaler.transform(earth[FEATURES_V1])

    (OUT / "matches").mkdir(parents=True, exist_ok=True)
    best_any = np.full(len(earth), np.inf)
    egypt_rows, out_targets = [], []
    for tgt in targets:
        site = mars[mars["site"] == tgt["name"]]
        sz = scaler.transform(site[FEATURES_V1])
        nn = NearestNeighbors(n_neighbors=NEIGHBOURS).fit(sz)
        dist, idx = nn.kneighbors(ez)
        d = dist.mean(axis=1)
        best_any = np.minimum(best_any, d)
        near = sz[idx].mean(axis=1)            # mean of the 10 nearest Mars tiles
        delta = ez - near

        ranked = earth.assign(distance=d).sort_values("distance")
        top = top_spread(ranked, TOP_N)
        rows = []
        for r in top.itertuples():
            i = r.idx
            rows.append({
                "lat": round(r.lat, 4), "lon": round(r.lon, 4),
                "country": r.country, "score": float(score(r.distance)),
                "features": {f: round(float(getattr(r, f)), 3)
                             for f in FEATURES_V1},
                "closeness": {f: float(c) for f, c in
                              zip(FEATURES_V1, closeness(delta[i]))},
            })
        (OUT / "matches" / f"{tgt['id']}.json").write_text(json.dumps(rows))

        eg = ranked[ranked["country"] == "Egypt"].head(1)
        if len(eg):
            r = eg.iloc[0]
            egypt_rows.append({"target": tgt["id"], "lat": round(r.lat, 4),
                               "lon": round(r.lon, 4),
                               "score": float(score(r.distance))})

        med = site[FEATURES_V1].median()
        out_targets.append({**tgt, "world": "mars",
                            "features": {f: round(float(med[f]), 3)
                                         for f in FEATURES_V1},
                            "best_score": rows[0]["score"] if rows else None})
        print(f"{tgt['name']:32s} best {rows[0]['score']:5.1f} "
              f"{rows[0]['country']}", flush=True)

    (OUT / "targets.json").write_text(json.dumps(
        {"features": [{"key": f, "label": FEATURE_LABELS[f], "unit": UNITS[f]}
                      for f in FEATURES_V1],
         "targets": out_targets}, indent=1))
    (OUT / "egypt.json").write_text(json.dumps(egypt_rows, indent=1))
    write_likeness(earth.assign(score=score(best_any)))
    return 0


def write_likeness(earth: pd.DataFrame) -> None:
    """A transparent PNG over Africa: brighter = more Mars-like."""
    from PIL import Image
    step = 1 / 12
    west, east, south, north = -18.0, 52.0, -35.0, 38.0
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
    Image.fromarray(img).save(OUT / "likeness.png", optimize=True)
    (OUT / "likeness.json").write_text(json.dumps(
        {"bounds": [[south, west], [north, east]]}))


if __name__ == "__main__":
    sys.exit(main())
