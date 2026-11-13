"""Profile NASA's nine Artemis III candidate landing regions with terrain only.

Reads src/targets/moon_artemis.json, cuts a LOLA patch around each region
(terrain.moon_patch, 463 m pixels, the same as Mars and Earth), and writes
one row per tile to data/processed/moon_artemis_v1.parquet: mean slope,
slope spread and relief. That file is an input of build_web_data.py.

Terrain only: there is no Moon albedo feature yet. Diviner thermal and LOLA
albedo are later upgrades (HANDOFF.md section 4).

Box size. The regions are small (most 20 x 20 km, Haworth 30 km, Mons Mouton
Plateau 67 km), and a tile must stay 20 pixels (9.26 km) to be comparable,
so a box cut to a region's outline would hold only about four tiles. Each
box is therefore the region's extent on the map plus MARGIN_M on every side
(the ground a crew would cross), at least MIN_BOX_PX, rounded up to whole
tiles. A box that would contain the pole is refused: it would mix in the
polar craters of several regions at once.

    python src/run_moon_targets.py
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path

import pandas as pd

import config
import terrain as t

TARGETS = Path(__file__).parent / "targets" / "moon_artemis.json"
OUT = config.PROCESSED / "moon_artemis_v1.parquet"
MARGIN_M = 15000.0
MIN_BOX_PX = 120


def load_regions() -> list[dict]:
    return json.loads(TARGETS.read_text(encoding="utf-8"))["regions"]


def box_px(region: dict) -> int:
    """Box side in 463 m pixels: extent + 2 x MARGIN_M, >= MIN_BOX_PX, whole
    tiles. The extent is measured on the map (the DEM's grid), then turned
    into ground metres with the map's scale at the region's latitude."""
    xy = [t.moon_xy(lat, lon) for lon, lat in region["outline"]]
    xs, ys = zip(*xy)
    extent_m = max(max(xs) - min(xs), max(ys) - min(ys)) / t.moon_scale(region["lat"])
    px = math.ceil((extent_m + 2 * MARGIN_M) / t.MOON_PIXEL_M / t.TILE_PX) * t.TILE_PX
    return max(MIN_BOX_PX, px)


def box_reaches_pole(region: dict, px: int) -> bool:
    x, y = t.moon_xy(region["lat"], region["lon"])
    half = px * t.MOON_PIXEL_M * t.moon_scale(region["lat"]) / 2
    return abs(x) < half and abs(y) < half


def main() -> None:
    parts = []
    for r in load_regions():
        px = box_px(r)
        if box_reaches_pole(r, px):
            print(f"SKIPPED {r['name']}: a {px} px box would contain the pole")
            continue
        t0 = time.time()
        try:
            cards = t.report_cards(t.moon_patch(r["lat"], r["lon"], px),
                                   t.MOON_PIXEL_M, t.MOON_PIXEL_M)
        except Exception as ex:  # one bad download should not stop the rest
            print(f"FAILED {r['name']}: {ex}")
            continue
        cards["site"] = r["name"]
        parts.append(cards)
        print(f"{r['name']:22s} box {px:3d} px ({px * t.MOON_PIXEL_M / 1000:5.1f} km) "
              f"{len(cards):4d} tiles   slope {cards.mean_slope.median():5.2f}   "
              f"relief {cards.relief.median():6.0f} m   {time.time() - t0:4.0f} s",
              flush=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    pd.concat(parts, ignore_index=True).to_parquet(OUT)
    print(f"\n{len(parts)} of {len(load_regions())} regions saved to {OUT}")


if __name__ == "__main__":
    main()
