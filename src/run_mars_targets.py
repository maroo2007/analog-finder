"""Profile NASA's candidate human landing zones on Mars with the V1 features.

Reads the 38 zones in src/targets/mars_human_ez.json (from the USGS CTX
Exploration Zone mosaics, duplicates removed), cuts a 400 x 400 pixel MOLA
patch (about 185 km) around each zone's centre, adds TES albedo, and writes
one row per tile to data/processed/mars_ez_v1.parquet. That file is the input
of build_web_data.py.

Nothing here needs an account: MOLA and TES are read straight from USGS.
A zone that fails to download is reported and skipped, so re-running is safe.

    python src/run_mars_targets.py
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd

import config
import surface as s
import terrain as t

TARGETS = Path(__file__).parent / "targets" / "mars_human_ez.json"
OUT = config.PROCESSED / "mars_ez_v1.parquet"


def main() -> None:
    zones = json.loads(TARGETS.read_text(encoding="utf-8"))
    parts = []
    for z in zones:
        t0 = time.time()
        try:
            cards = t.report_cards(
                t.mars_patch(z["lat"], z["lon"]), t.MARS_PIXEL_M,
                t.MARS_PIXEL_M,
                layers={"albedo": s.mars_albedo(z["lat"], z["lon"])})
        except Exception as ex:  # one bad download should not stop the rest
            print(f"FAILED {z['name']}: {ex}")
            continue
        cards["site"] = z["name"]
        parts.append(cards)
        print(f"{z['name']:32s} {len(cards):4d} tiles   "
              f"slope {cards.mean_slope.median():5.2f}   "
              f"albedo {cards.albedo.median():.3f}   {time.time() - t0:4.0f} s",
              flush=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    pd.concat(parts, ignore_index=True).to_parquet(OUT)
    print(f"\n{len(parts)} of {len(zones)} zones saved to {OUT}")


if __name__ == "__main__":
    main()
