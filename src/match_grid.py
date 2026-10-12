"""Rank Earth grid tiles by how closely they match each Mars site, with V1.

V1 features: mean slope, slope spread, relief and absolute albedo, compared
only on Mars-possible Earth tiles. Features are standardized the same way as
run_thermal.match: z-scores fitted on the Earth tiles and the Mars tiles
together.

A tile's distance to a Mars site is its mean distance to the site's
NEIGHBOURS nearest Mars tiles, so a tile only has to resemble part of a site
(a crater floor, say), not the whole. Lower is closer.

    python src/match_grid.py egypt Jezero Gale
"""

from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

import config
import earth_grid as g
import surface as s
import terrain as t
from run_phase1 import MARS_SITES
from run_thermal import FEATURES_V1

NEIGHBOURS = 10
MIN_SPACING_DEG = 0.25     # about 25 km between listed tiles


def mars_cards() -> pd.DataFrame:
    """V1 report cards for the Phase 1 Mars sites. Cached in data/processed/."""
    path = config.PROCESSED / "mars_sites_v1.parquet"
    if path.exists():
        return pd.read_parquet(path)
    parts = []
    for name, (lat, lon) in MARS_SITES.items():
        cards = t.report_cards(t.mars_patch(lat, lon), t.MARS_PIXEL_M,
                               t.MARS_PIXEL_M,
                               layers={"albedo": s.mars_albedo(lat, lon)})
        cards["site"] = name
        parts.append(cards)
    mars = pd.concat(parts, ignore_index=True)
    mars.to_parquet(path)
    return mars


def rank(grid: pd.DataFrame, mars: pd.DataFrame, site: str) -> pd.DataFrame:
    """Every Mars-possible Earth tile, closest to `site` first."""
    earth = grid[grid["mars_possible"]].dropna(subset=FEATURES_V1).copy()
    mars = mars.dropna(subset=FEATURES_V1)
    scaler = StandardScaler().fit(pd.concat([earth[FEATURES_V1],
                                             mars[FEATURES_V1]]))
    site_tiles = scaler.transform(mars.loc[mars["site"] == site, FEATURES_V1])
    finder = NearestNeighbors(n_neighbors=NEIGHBOURS).fit(site_tiles)
    dist, _ = finder.kneighbors(scaler.transform(earth[FEATURES_V1]))
    earth["distance"] = dist.mean(axis=1)
    return earth.sort_values("distance").reset_index(drop=True)


def top_spread(ranked: pd.DataFrame, n: int = 5,
               spacing: float = MIN_SPACING_DEG) -> pd.DataFrame:
    """The n best tiles, skipping any within `spacing` degrees of one already
    picked, so the list is not five neighbours of the same spot."""
    picked = []
    for row in ranked.itertuples():
        if all(max(abs(row.lat - p.lat), abs(row.lon - p.lon)) >= spacing
               for p in picked):
            picked.append(row)
            if len(picked) == n:
                break
    return pd.DataFrame(picked).drop(columns="Index")


def maps_link(lat: float, lon: float) -> str:
    """Google Maps, satellite view, centred on the tile."""
    return ("https://www.google.com/maps/@?api=1&map_action=map"
            f"&center={lat:.4f},{lon:.4f}&zoom=12&basemap=satellite")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("area", choices=list(g.AREAS))
    parser.add_argument("sites", nargs="+", choices=list(MARS_SITES))
    parser.add_argument("-n", type=int, default=5)
    args = parser.parse_args()

    grid, mars = g.load(args.area), mars_cards()
    have = grid["mars_possible"] & grid["mean_slope"].notna()
    print(f"{args.area}: {len(grid)} land tiles, {int(grid.mars_possible.sum())} "
          f"Mars-possible, {int(have.sum())} with terrain")
    for site in args.sites:
        best = top_spread(rank(grid, mars, site), args.n)
        site_alb = mars.loc[mars.site == site, "albedo"].median()
        print(f"\n{site} (Mars albedo median {site_alb:.3f}): top {len(best)}")
        for i, r in enumerate(best.itertuples(), 1):
            print(f"  {i}. {r.lat:.4f}, {r.lon:.4f}  distance {r.distance:.2f}  "
                  f"slope {r.mean_slope:.1f} deg  relief {r.relief:.0f} m  "
                  f"albedo {r.albedo:.3f}  ndvi {r.ndvi:.3f}")
            print(f"     {maps_link(r.lat, r.lon)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
