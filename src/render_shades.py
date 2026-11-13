"""Render the hillshade pairs the interface's twin view swipes between.

Each Mars zone or Moon region, and each of its Earth twins, is drawn the
same way: elevation
at 463 m per pixel (the resolution the matching uses), a 65 km square, the
same sun (azimuth 315, elevation 45) and no vertical exaggeration. So any
difference you see is in the ground, not in how it was drawn.

    python src/render_shades.py            # targets, best twin, Egypt (PNG)
    python src/render_shades.py --twins    # every twin, as small WebP

--twins draws all 25 twins of every target, its Egyptian tile and the
target itself as 200 px WebP: shade/earth/<target>_<n>.webp, where n is
the twin's place (1 to 25) in matches/<target>.json, so _1 is the same tile
as _top; shade/earth/<target>_egypt.webp; shade/<world>/<target>.webp. It
skips files that exist, so it can be stopped and run again.
"""

from __future__ import annotations

import io
import json
import math
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

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
TWIN_PX = 200                      # the per-twin WebP images
WEBP_QUALITY = 80
WORKERS = 6                        # threads; the time is spent downloading
TINTS = {"mars": (255, 214, 180), "moon": (225, 225, 225)}
EARTH_TINT = (205, 225, 230)
# How files are fetched, not what is read: no directory listing per open
# (as in terrain.moon_patch) and a retry on a dropped connection.
GDAL_OPTS = {"GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
             "GDAL_HTTP_MAX_RETRY": 3, "GDAL_HTTP_RETRY_DELAY": 2}


def hillshade(z: np.ndarray, px_x: float, px_y: float) -> np.ndarray:
    z = np.where(np.isfinite(z), z, np.nanmedian(z))
    gy, gx = np.gradient(z, px_y, px_x)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    az, alt = math.radians(315), math.radians(45)
    shade = (math.sin(alt) * np.cos(slope)
             + math.cos(alt) * np.sin(slope) * np.cos(az - aspect))
    return np.clip(shade, 0, 1)


def _tinted(shade: np.ndarray, tint, px: int) -> Image.Image:
    rgb = (shade[..., None] * np.array(tint)[None, None, :]).clip(0, 255)
    return Image.fromarray(rgb.astype(np.uint8)).resize((px, px), Image.BICUBIC)


def to_png(shade: np.ndarray, tint, path) -> None:
    img = _tinted(shade, tint, OUT_PX)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, optimize=True)


def webp_bytes(shade: np.ndarray, tint) -> bytes:
    buf = io.BytesIO()
    _tinted(shade, tint, TWIN_PX).save(buf, "WEBP", quality=WEBP_QUALITY,
                                       method=6)
    return buf.getvalue()


def _write(path, blob: bytes) -> None:
    """Write via a .part file, so a stopped run never leaves a half-written
    image that the next run would skip as done."""
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + ".part")
    part.write_bytes(blob)
    part.replace(path)


def earth_window(lat: float, lon: float) -> tuple[np.ndarray, float, float]:
    half_m = SIZE_PX * t.MARS_PIXEL_M / 2
    dlat = half_m / t.EARTH_METRES_PER_DEG
    dlon = dlat / math.cos(math.radians(lat))
    west, east, south, north = lon - dlon, lon + dlon, lat - dlat, lat + dlat
    srcs = []
    with rasterio.Env(**GDAL_OPTS):                    # per thread
        for la in range(math.floor(south), math.floor(north) + 1):
            for lo in range(math.floor(west), math.floor(east) + 1):
                try:
                    srcs.append(rasterio.open(COP.format(n=t._cop_tile_name(la, lo))))
                except rasterio.errors.RasterioIOError:
                    pass                               # ocean: no tile
        arr, _ = merge(srcs, bounds=(west, south, east, north),
                       res=((east - west) / SIZE_PX, (north - south) / SIZE_PX),
                       resampling=Resampling.average, nodata=np.nan,
                       dtype="float32")
        for s in srcs:
            s.close()
    z = arr[0][:SIZE_PX, :SIZE_PX]
    px = t.MARS_PIXEL_M
    return z, px, px


def target_shade(tgt: dict) -> np.ndarray:
    patch = t.moon_patch if tgt["world"] == "moon" else t.mars_patch
    z = patch(tgt["lat"], tgt["lon"], SIZE_PX)
    return hillshade(z, t.MARS_PIXEL_M, t.MARS_PIXEL_M)


def twin_files(data, targets) -> dict:
    """Every Earth WebP to make, grouped by point: {(lat, lon): [paths]}.
    A tile can be a twin of several targets; it is drawn once."""
    egypt = {e["target"]: e for e in
             json.loads((data / "egypt.json").read_text(encoding="utf-8"))}
    points: dict = {}
    for tgt in targets:
        tid = tgt["id"]
        rows = json.loads((data / "matches" / f"{tid}.json").read_text(encoding="utf-8"))
        named = [(f"{tid}_{n}.webp", m) for n, m in enumerate(rows, 1)]
        if tid in egypt:
            named.append((f"{tid}_egypt.webp", egypt[tid]))
        for name, m in named:
            points.setdefault((m["lat"], m["lon"]), []).append(OUT / "earth" / name)
    return points


def render_twins(data, targets, workers: int = WORKERS) -> int:
    points = twin_files(data, targets)
    todo = {}
    for pt, paths in points.items():
        missing = [p for p in paths if not p.exists()]
        have = [p for p in paths if p.exists()]
        if missing and have:                 # drawn already for another target
            for p in missing:
                _write(p, have[0].read_bytes())
        elif missing:
            todo[pt] = missing
    n_files = sum(len(p) for p in points.values())
    print(f"{n_files} Earth images at {len(points)} distinct points; "
          f"{len(todo)} points left to draw, {workers} threads", flush=True)

    def draw(pt):
        z, px, py = earth_window(*pt)
        return webp_bytes(hillshade(z, px, py), EARTH_TINT)

    failed, t0 = [], time.time()
    with ThreadPoolExecutor(workers) as pool:
        jobs = {pool.submit(draw, pt): pt for pt in todo}
        for done, job in enumerate(as_completed(jobs), 1):
            pt = jobs[job]
            try:
                blob = job.result()
                for p in todo[pt]:
                    _write(p, blob)
                note = " ".join(p.stem for p in todo[pt])
            except Exception as e:               # keep going; a rerun retries
                failed.append(pt)
                note = f"FAILED {type(e).__name__}: {e}"
            mins = (time.time() - t0) / 60
            left = mins / done * (len(todo) - done)
            print(f"[{done}/{len(todo)}] ({pt[0]:.4f}, {pt[1]:.4f}) {note}"
                  f"  {mins:.1f} min, about {left:.0f} min left", flush=True)

    for tgt in targets:                      # the target side of each pair
        path = OUT / tgt["world"] / f"{tgt['id']}.webp"
        if path.exists():
            continue
        try:
            _write(path, webp_bytes(target_shade(tgt), TINTS[tgt["world"]]))
            print(f"target {tgt['id']} ok", flush=True)
        except Exception as e:
            failed.append(tgt["id"])
            print(f"target {tgt['id']} FAILED {type(e).__name__}: {e}", flush=True)
    print(f"done in {(time.time() - t0) / 60:.1f} min; failed: {failed or 'none'}",
          flush=True)
    return 1 if failed else 0


def main() -> int:
    """python src/render_shades.py [--world mars|moon] [--twins [--workers N]]"""
    data = config.ROOT / "web" / "public" / "data"
    targets = json.loads((data / "targets.json").read_text(encoding="utf-8"))["targets"]
    if "--world" in sys.argv:
        world = sys.argv[sys.argv.index("--world") + 1]
        targets = [x for x in targets if x["world"] == world]
    if "--twins" in sys.argv:
        workers = (int(sys.argv[sys.argv.index("--workers") + 1])
                   if "--workers" in sys.argv else WORKERS)
        return render_twins(data, targets, workers)
    egypt = {e["target"]: e for e in
             json.loads((data / "egypt.json").read_text(encoding="utf-8"))}
    for tgt in targets:
        tid, world = tgt["id"], tgt["world"]
        to_png(target_shade(tgt), TINTS[world], OUT / world / f"{tid}.png")
        top = json.loads((data / "matches" / f"{tid}.json").read_text())[0]
        for kind, pt in (("top", top), ("egypt", egypt.get(tid))):
            if pt is None:
                continue
            z, px, py = earth_window(pt["lat"], pt["lon"])
            to_png(hillshade(z, px, py), EARTH_TINT,
                   OUT / "earth" / f"{tid}_{kind}.png")
        print(tid, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
