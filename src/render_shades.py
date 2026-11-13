"""Render the hillshade pairs the interface's twin view swipes between.

Each Mars zone or Moon region, and each of its Earth twins, is drawn the
same way: elevation
at 463 m per pixel (the resolution the matching uses), a 65 km square, the
same sun (azimuth 315, elevation 45) and no vertical exaggeration. So any
difference you see is in the ground, not in how it was drawn.

    python src/render_shades.py
"""

from __future__ import annotations

import json
import math
import sys

import numpy as np
import rasterio
from PIL import Image
from rasterio.enums import Resampling
from rasterio.merge import merge

import config
import terrain as t

OUT = config.ROOT / "web" / "public" / "data" / "shade"
SIZE_PX = 140                      # 140 x 463 m = 65 km
OUT_PX = 280
COP = ("/vsicurl/https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com/"
       "{n}/{n}.tif")


def hillshade(z: np.ndarray, px_x: float, px_y: float) -> np.ndarray:
    z = np.where(np.isfinite(z), z, np.nanmedian(z))
    gy, gx = np.gradient(z, px_y, px_x)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    az, alt = math.radians(315), math.radians(45)
    shade = (math.sin(alt) * np.cos(slope)
             + math.cos(alt) * np.sin(slope) * np.cos(az - aspect))
    return np.clip(shade, 0, 1)


def to_png(shade: np.ndarray, tint, path) -> None:
    rgb = (shade[..., None] * np.array(tint)[None, None, :]).clip(0, 255)
    img = Image.fromarray(rgb.astype(np.uint8)).resize((OUT_PX, OUT_PX),
                                                       Image.BICUBIC)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, optimize=True)


def earth_window(lat: float, lon: float) -> tuple[np.ndarray, float, float]:
    half_m = SIZE_PX * t.MARS_PIXEL_M / 2
    dlat = half_m / t.EARTH_METRES_PER_DEG
    dlon = dlat / math.cos(math.radians(lat))
    west, east, south, north = lon - dlon, lon + dlon, lat - dlat, lat + dlat
    srcs = []
    for la in range(math.floor(south), math.floor(north) + 1):
        for lo in range(math.floor(west), math.floor(east) + 1):
            try:
                srcs.append(rasterio.open(COP.format(n=t._cop_tile_name(la, lo))))
            except rasterio.errors.RasterioIOError:
                pass                                   # ocean: no tile
    arr, _ = merge(srcs, bounds=(west, south, east, north),
                   res=((east - west) / SIZE_PX, (north - south) / SIZE_PX),
                   resampling=Resampling.average, nodata=np.nan,
                   dtype="float32")
    for s in srcs:
        s.close()
    z = arr[0][:SIZE_PX, :SIZE_PX]
    px = t.MARS_PIXEL_M
    return z, px, px


def main() -> int:
    """python src/render_shades.py [--world mars|moon]   (default: both)"""
    data = config.ROOT / "web" / "public" / "data"
    targets = json.loads((data / "targets.json").read_text(encoding="utf-8"))["targets"]
    if "--world" in sys.argv:
        world = sys.argv[sys.argv.index("--world") + 1]
        targets = [x for x in targets if x["world"] == world]
    egypt = {e["target"]: e for e in
             json.loads((data / "egypt.json").read_text(encoding="utf-8"))}
    tints = {"mars": (255, 214, 180), "moon": (225, 225, 225)}
    earth_tint = (205, 225, 230)
    for tgt in targets:
        tid, world = tgt["id"], tgt["world"]
        patch = t.moon_patch if world == "moon" else t.mars_patch
        z = patch(tgt["lat"], tgt["lon"], SIZE_PX)
        to_png(hillshade(z, t.MARS_PIXEL_M, t.MARS_PIXEL_M), tints[world],
               OUT / world / f"{tid}.png")
        top = json.loads((data / "matches" / f"{tid}.json").read_text())[0]
        for kind, pt in (("top", top), ("egypt", egypt.get(tid))):
            if pt is None:
                continue
            z, px, py = earth_window(pt["lat"], pt["lon"])
            to_png(hillshade(z, px, py), earth_tint,
                   OUT / "earth" / f"{tid}_{kind}.png")
        print(tid, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
