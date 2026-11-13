"""Score the whole Earth: one V1 feature row for every Mars-possible land tile.

Tiles are 1/12 degree squares (about 9.26 km), lined up exactly like the
Phase 1 Earth tiles in terrain.report_cards: 20 pixels of 1/240 degree, the
same pixel size as MOLA (463 m).

Three stages, so expensive work only happens where it can matter:

  A. ndvi      Earth Engine, every land tile: lat, lon, country, ndvi, from
               MODIS's coarse 0.05 degree NDVI (MOD13C1). Cheap.
  B. surface   Earth Engine, only tiles with ndvi below NDVI_MAX: permanent
               water fraction (JRC, 30 m), albedo (MCD43C3, 0.05 degree) and
               permanent snow and ice fraction (MCD12Q1, 500 m; areas run
               from 13 November 2026 on).
               Water is the expensive layer, so it never touches ocean or
               green land.
  C. terrain   This laptop, no Earth Engine quota: mean slope, slope spread
               and relief for every 1 degree square that holds a
               Mars-possible tile, with exactly the code the validation
               uses (terrain.earth_patch + report_cards, Copernicus DEM on
               AWS, average resampling). One small file per square, so a
               stopped run resumes where it left off.

Every Earth Engine task runs under a cost cap: it is polled every
POLL_SECONDS and cancelled the moment its compute passes the cap. A run that
exceeded its estimate cost 14.7 EECU-hours on 10 October; see HANDOFF.md.

    python src/earth_grid.py run egypt --cap 1      A and B, capped, then C
    python src/earth_grid.py run americas --cap 0.5 --ndvi-only
                                                    A only, prints stage B's
                                                    workload to estimate it
    python src/earth_grid.py run americas --cap 6 --reuse-ndvi
                                                    B on the saved A, then C
    python src/earth_grid.py terrain africa         C only (resumable)
    python src/earth_grid.py status                 tasks and compute used
"""

from __future__ import annotations

import argparse
import math
import sys
import time

import numpy as np
import pandas as pd

import config
import surface as s
import terrain as t

ALBEDO = "MODIS/061/MCD43C3"          # 0.05 degree daily albedo
NDVI = "MODIS/061/MOD13C1"            # 0.05 degree 16-day NDVI
WATER = "JRC/GSW1_4/GlobalSurfaceWater"
LAND_COVER = "MODIS/061/MCD12Q1"        # 500 m yearly land cover
ICE_CLASS = 15                          # IGBP: permanent snow and ice
ICE_START = "2021-01-01"                # five yearly maps (2021-2025), mode
COUNTRIES = "USDOS/LSIB_SIMPLE/2017"

FINE_DEG = 1.0 / 240.0                  # 463 m at the equator, as MOLA
TILE_DEG = 1.0 / 12.0                   # 20 fine pixels, as TILE_PX
LAT_LIMIT = 85.0
POLL_SECONDS = 10   # a runaway task burned ~4 EECU-hours a minute

ASSET_FOLDER = f"projects/{config.EE_PROJECT}/assets/earth_grid"
GRID_DIR = config.PROCESSED / "earth_grid"

# Areas: which LSIB property selects the countries, the values, and a box
# that covers the land (the country mask does the rest).
AREAS = {
    "egypt": ("country_na", ["Egypt"], [24.5, 21.5, 37.5, 32.0]),
    "africa": ("wld_rgn", ["Africa"], [-26.0, -47.0, 64.0, 38.0]),
    # Test area for the Americas: coast and sea, the Andes and the Atacama.
    "chile": ("country_na", ["Chile"], [-76.0, -56.5, -66.0, -17.0]),
    # The Americas south of 50 N (Death Valley, Utah, Mexico, the Andes,
    # Atacama, Patagonia). Further north, snow makes median NDVI near zero,
    # so the filter would let in tundra and ice. Hawaii is outside the box.
    "americas": ("wld_rgn", ["North America", "Central America", "Caribbean",
                             "South America"], [-125.0, -56.5, -34.0, 50.0]),
}

FEATURE_COLUMNS = ["mean_slope", "slope_spread", "relief", "albedo"]


# ============================================================ Earth Engine

def _grid(ee, step):
    """A lat/lon grid with cells `step` degrees wide, aligned to whole
    degrees, like terrain.earth_patch."""
    return ee.Projection("EPSG:4326", [step, 0, -180, 0, -step, 90])


def _median(ee, asset, band, scale):
    """Median over the shared date range, in physical units, keeping the
    product's own pixel grid (a median forgets it, and averaging into tiles
    needs it)."""
    coll = ee.ImageCollection(asset).filterDate(s.DATE_START, s.DATE_END)
    return (coll.select(band).median().multiply(scale)
            .setDefaultProjection(coll.first().select(band).projection()))


def _to_tile(ee, img):
    return (img.reduceResolution(ee.Reducer.mean(), maxPixels=1024)
            .reproject(_grid(ee, TILE_DEG)))


def ndvi_table(ee, area):
    """Stage A: every land tile of the area with lat, lon, country, ndvi."""
    prop, values, box = AREAS[area]
    fc = ee.FeatureCollection(COUNTRIES).filter(ee.Filter.inList(prop, values))
    names = fc.aggregate_array("country_na").distinct().sort()
    fc = fc.map(lambda f: f.set("cid", names.indexOf(f.get("country_na"))))
    tile = _grid(ee, TILE_DEG)
    cid = ee.Image().int().paint(fc, "cid").rename("cid").reproject(tile)

    # Earth Engine stores MOD13C1 NDVI already scaled (unlike MOD13A2 in
    # surface.py, which needs x 0.0001), so the factor here is 1.
    ndvi = _to_tile(ee, _median(ee, NDVI, "NDVI", 1.0)).rename("ndvi")
    lonlat = ee.Image.pixelLonLat().reproject(tile).rename(["lon", "lat"])
    img = ee.Image.cat([lonlat, ndvi, cid]).toFloat().updateMask(cid.mask())

    west, south, east, north = box
    rect = ee.Geometry.Rectangle(
        [west, max(south, -LAT_LIMIT), east, min(north, LAT_LIMIT)], None, False)
    # geometries=True: an asset table refuses rows without a location.
    samples = img.sample(region=rect, projection=tile, dropNulls=True,
                         geometries=True, tileScale=4)
    samples = samples.map(lambda f: f.set(
        "country", names.get(ee.Number(f.get("cid")).int())))
    return samples.select(["lat", "lon", "country", "ndvi"])


def surface_table(ee, area):
    """Stage B: water fraction and albedo, only where stage A's ndvi passes."""
    passed = (ee.FeatureCollection(f"{ASSET_FOLDER}/{area}_ndvi")
              .filter(ee.Filter.lt("ndvi", s.NDVI_MAX)))
    # Permanent water (all twelve months), as in surface.py. JRC is 30 m: two
    # averaging steps, because 30 m to 9 km is too many pixels at once.
    water = _to_tile(ee, (ee.Image(WATER).select("seasonality").eq(12)
                          .unmask(0).reduceResolution(ee.Reducer.mean(),
                                                      maxPixels=1024)
                          .reproject(_grid(ee, FINE_DEG)))).rename("water")
    albedo = _to_tile(ee, _median(ee, ALBEDO, "Albedo_WSA_shortwave", 0.001)
                      ).rename("albedo")
    # Permanent snow and ice fraction: the land cover class each 500 m pixel
    # has most often over the recent years, 1 where it is ice, averaged into
    # the tile. 500 m to 9 km is about 400 pixels, within one averaging step.
    lc = (ee.ImageCollection(LAND_COVER).filterDate(ICE_START, s.DATE_END)
          .select("LC_Type1"))
    ice = _to_tile(ee, lc.mode().eq(ICE_CLASS)
                   .setDefaultProjection(lc.first().projection())).rename("ice")
    # tileScale=16 (the maximum) keeps each block of work small enough: the
    # 30 m water layer overflows Earth Engine's 2^31-pixel limit otherwise.
    return (ee.Image.cat([water, albedo, ice]).toFloat()
            .sampleRegions(collection=passed, projection=_grid(ee, TILE_DEG),
                           tileScale=16, geometries=True)
            .select(["lat", "lon", "water", "albedo", "ice"]))


def _ensure_folder(ee):
    try:
        ee.data.getAsset(ASSET_FOLDER)
    except ee.EEException:
        ee.data.createAsset({"type": "FOLDER"}, ASSET_FOLDER)


def _operation(ee, description):
    """The most recent operation with this description."""
    ops = [op for op in ee.data.listOperations()
           if op.get("metadata", {}).get("description") == description]
    return max(ops, key=lambda op: op["metadata"].get("createTime", ""))


def run_capped(ee, table, name, cap_hours: float) -> dict:
    """Export `table` to an asset, cancelling it the moment its compute passes
    `cap_hours` EECU-hours. Returns state and EECU-hours; raises if the task
    failed or was cancelled."""
    _ensure_folder(ee)
    description = f"earth_grid_{name}"
    task = ee.batch.Export.table.toAsset(
        collection=table, description=description,
        assetId=f"{ASSET_FOLDER}/{name}")
    task.start()
    print(f"started {description}, cap {cap_hours} EECU-hours", flush=True)
    while True:
        time.sleep(POLL_SECONDS)
        op = _operation(ee, description)
        meta = op["metadata"]
        used = meta.get("batchEecuUsageSeconds", 0) / 3600
        state = meta.get("state")
        if state in ("PENDING", "RUNNING") and used > cap_hours:
            ee.data.cancelOperation(op["name"])
            raise RuntimeError(f"{description} cancelled: {used:.3f} EECU-hours "
                               f"passed the cap of {cap_hours}")
        if state not in ("PENDING", "RUNNING", "CANCELLING"):
            print(f"{description}: {state}, {used:.4f} EECU-hours", flush=True)
            if state != "SUCCEEDED":
                raise RuntimeError(f"{description} {state}: "
                                   f"{op.get('error', {}).get('message')}")
            return {"state": state, "eecu_hours": used}


def status() -> pd.DataFrame:
    """Recent earth_grid tasks with state and compute used (EECU-hours)."""
    ee = config.init_ee()
    rows = []
    for op in ee.data.listOperations():
        meta = op.get("metadata", {})
        desc = meta.get("description", "")
        if not desc.startswith("earth_grid_"):
            continue
        rows.append({
            "task": desc,
            "state": meta.get("state"),
            "eecu_hours": meta.get("batchEecuUsageSeconds", 0) / 3600,
            "started": meta.get("startTime"),
            "updated": meta.get("updateTime"),
            "error": op.get("error", {}).get("message"),
        })
    return pd.DataFrame(rows)


def _read(ee, asset_id) -> pd.DataFrame:
    return ee.data.computeFeatures({
        "expression": ee.FeatureCollection(asset_id),
        "fileFormat": "PANDAS_DATAFRAME",
    })


def _key(df: pd.DataFrame) -> pd.Series:
    """Tile key from its centre, robust to float noise."""
    return (np.floor(df["lat"] / TILE_DEG).astype(int).astype(str) + "_"
            + np.floor(df["lon"] / TILE_DEG).astype(int).astype(str))


def ndvi_counts(ee, area) -> dict:
    """After stage A: land tiles, tiles that pass NDVI (stage B's workload,
    which sets its cost), and the passing tiles per country. Small
    interactive queries on the finished table, not an export."""
    table = ee.FeatureCollection(f"{ASSET_FOLDER}/{area}_ndvi")
    passed = table.filter(ee.Filter.lt("ndvi", s.NDVI_MAX))
    return ee.Dictionary({
        "land_tiles": table.size(), "pass_ndvi": passed.size(),
        "pass_by_country": passed.aggregate_histogram("country"),
    }).getInfo()


def run_earth_engine(area: str, cap_hours: float, ndvi_only: bool = False,
                     reuse_ndvi: bool = False) -> pd.DataFrame | dict:
    """Stages A and B under one total cap; returns the joined table.

    ndvi_only: run stage A alone and return its counts, so stage B's cost
    can be estimated from its real workload before it runs.
    reuse_ndvi: skip stage A and use the stage A table already saved.
    """
    ee = config.init_ee()
    if reuse_ndvi:
        ee.data.getAsset(f"{ASSET_FOLDER}/{area}_ndvi")   # fails if missing
        a = {"eecu_hours": 0.0}
        print(f"reusing {area}_ndvi from an earlier stage A", flush=True)
    else:
        a = run_capped(ee, ndvi_table(ee, area), f"{area}_ndvi", cap_hours)
    if ndvi_only:
        return {"eecu_hours": a["eecu_hours"], **ndvi_counts(ee, area)}
    b = run_capped(ee, surface_table(ee, area), f"{area}_surface",
                   cap_hours - a["eecu_hours"])
    print(f"Earth Engine total for {area}: "
          f"{a['eecu_hours'] + b['eecu_hours']:.4f} EECU-hours", flush=True)

    ndvi = _read(ee, f"{ASSET_FOLDER}/{area}_ndvi")[["lat", "lon", "country", "ndvi"]]
    surf = _read(ee, f"{ASSET_FOLDER}/{area}_surface")
    surf = surf[[c for c in ("lat", "lon", "water", "albedo", "ice") if c in surf]]
    ndvi["k"], surf["k"] = _key(ndvi), _key(surf)
    df = ndvi.merge(surf.drop(columns=["lat", "lon"]), on="k", how="left")
    df["mars_possible"] = s.mars_possible(df)
    GRID_DIR.mkdir(parents=True, exist_ok=True)
    df.drop(columns="k").to_parquet(GRID_DIR / f"{area}_surface.parquet")
    return df.drop(columns="k")


# ============================================================ local terrain

def _square_name(lat0: int, lon0: int) -> str:
    return f"{'N' if lat0 >= 0 else 'S'}{abs(lat0):02d}_{'E' if lon0 >= 0 else 'W'}{abs(lon0):03d}"


def terrain_square(lat0: int, lon0: int) -> pd.DataFrame:
    """Terrain for every tile of one 1 degree square, as the validation does."""
    elev, px_x, px_y = t.earth_patch(lat0 + 0.5, lon0 + 0.5)
    cards = t.report_cards(elev, px_x, px_y)
    half = t.TILE_PX / 2
    cards["lat"] = lat0 + 1 - (cards["row"] + half) * FINE_DEG
    cards["lon"] = lon0 + (cards["col"] + half) * FINE_DEG
    return cards[["lat", "lon"] + t.FEATURES]


def run_terrain(area: str, retries: int = 3) -> None:
    """Stage C for every square holding a Mars-possible tile. Resumable: a
    square with a file in terrain/ is skipped. A square with no Copernicus
    file (open ocean) gets an empty file, so it is not tried again."""
    surface = pd.read_parquet(GRID_DIR / f"{area}_surface.parquet")
    wanted = surface[surface["mars_possible"]]
    squares = sorted({(math.floor(a), math.floor(o))
                      for a, o in zip(wanted["lat"], wanted["lon"])})
    out_dir = GRID_DIR / "terrain"
    out_dir.mkdir(parents=True, exist_ok=True)
    todo = [sq for sq in squares
            if not (out_dir / f"{_square_name(*sq)}.parquet").exists()]
    print(f"{area}: {len(squares)} squares needed, {len(squares) - len(todo)} "
          f"already done, {len(todo)} to go", flush=True)

    start, failed = time.time(), []
    for i, (lat0, lon0) in enumerate(todo, 1):
        path = out_dir / f"{_square_name(lat0, lon0)}.parquet"
        for attempt in range(1, retries + 1):
            try:
                cards = terrain_square(lat0, lon0)
                break
            except Exception as exc:  # network hiccup or missing file
                missing = "404" in str(exc) or "not recognized" in str(exc)
                if missing:
                    cards = pd.DataFrame(columns=["lat", "lon"] + t.FEATURES)
                    break
                if attempt == retries:
                    cards = None
                    failed.append((lat0, lon0, str(exc)[:120]))
                else:
                    time.sleep(10 * attempt)
        if cards is not None:
            cards.to_parquet(path)
        if i % 25 == 0 or i == len(todo):
            rate = (time.time() - start) / i
            print(f"  {i}/{len(todo)} squares, {rate:.1f} s each, "
                  f"about {rate * (len(todo) - i) / 60:.0f} min left", flush=True)
    if failed:
        print(f"{len(failed)} squares failed after {retries} tries "
              f"(rerun to retry): {failed[:5]}", flush=True)


def load(area: str) -> pd.DataFrame:
    """The full grid for an area: surface stages joined with local terrain."""
    surface = pd.read_parquet(GRID_DIR / f"{area}_surface.parquet")
    parts = [pd.read_parquet(p) for p in (GRID_DIR / "terrain").glob("*.parquet")]
    terr = pd.concat([p for p in parts if len(p)], ignore_index=True)
    surface["k"], terr["k"] = _key(surface), _key(terr)
    df = surface.merge(terr.drop(columns=["lat", "lon"]), on="k", how="left")
    return df.drop(columns="k")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run")
    run.add_argument("area", choices=list(AREAS))
    run.add_argument("--cap", type=float, required=True,
                     help="EECU-hours; Earth Engine tasks are cancelled above it")
    run.add_argument("--ndvi-only", action="store_true",
                     help="stage A only, then print the counts stage B's "
                          "cost depends on")
    run.add_argument("--reuse-ndvi", action="store_true",
                     help="skip stage A and use the saved stage A table")
    sub.add_parser("terrain").add_argument("area", choices=list(AREAS))
    sub.add_parser("status")
    args = parser.parse_args()

    if args.cmd == "run" and args.ndvi_only:
        c = run_earth_engine(args.area, args.cap, ndvi_only=True,
                             reuse_ndvi=args.reuse_ndvi)
        print(f"stage A: {c['eecu_hours']:.4f} EECU-hours, {c['land_tiles']:,} "
              f"land tiles, {c['pass_ndvi']:,} pass NDVI "
              f"({c['pass_ndvi'] / max(c['land_tiles'], 1):.0%})")
        for name, n in sorted(c["pass_by_country"].items(), key=lambda x: -x[1]):
            print(f"  {name:32s} {n:7,}")
    elif args.cmd == "run":
        df = run_earth_engine(args.area, args.cap, reuse_ndvi=args.reuse_ndvi)
        print(f"{len(df)} land tiles, {int(df.mars_possible.sum())} Mars-possible",
              flush=True)
        run_terrain(args.area)
    elif args.cmd == "terrain":
        run_terrain(args.area)
    else:
        print(status().to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
