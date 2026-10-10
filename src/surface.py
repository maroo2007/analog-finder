"""Heat, brightness, and the "could this be Mars" filter.

Phase 1 only saw the shape of the ground, so it could not tell a flat Martian
plain from flat green farmland. This module adds three things:

  A. mars_possible  Earth only. Mars has no plants and no surface water, so an
                    Earth tile that is green or wet is never offered as a twin.
  B. albedo         How much light the ground reflects, compared directly in
                    physical units (0 to 1) because both worlds measure the
                    same quantity. Earth: MODIS white-sky shortwave albedo.
                    Mars: TES albedo. Different instruments and atmospheres,
                    so treat small differences with caution.
  C. heat           How well the ground holds heat.
                    Earth: apparent thermal inertia from MODIS,
                        ATI = (1 - albedo) / (T_day - T_night)
                    Mars: THEMIS night-time infrared. Ground that stays bright
                        (warm) at night holds heat: rock and crusts. Ground that
                        goes dark is dust and fine sand. It is an 8-bit
                        qualitative mosaic, not calibrated thermal inertia; the
                        quantitative THEMIS thermal inertia mosaic returns 404.
                    Not a matching feature: on Earth ATI mostly tracks soil
                    moisture, on Mars rock versus dust, so the two are not
                    comparable. Used only to label Mars tiles dusty, sandy or
                    rocky (ground_label), and in the experimental V2 in
                    run_thermal.py. Earth tiles get no label until there is a
                    better Earth heat measure.

Heat is only ever compared as a percentile within a world. The Earth reference
is bare, dry land only (passing the same filter), because all of Mars is bare
and dry: ranking Earth deserts against all land, farms and forests included,
put them at the extremes and failed (see HANDOFF.md). Reference samples use
ground between 60N and 60S, because the THEMIS mosaic only covers that band.

Memory: Earth layers are computed on Earth Engine's servers and only a
240 x 240 grid per region comes back. Mars reads are small windows, apart from
the whole TES albedo map (2880 x 1440, about 17 MB) for the Mars reference.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import rasterio
from pyproj import CRS
from rasterio.enums import Resampling
from rasterio.windows import from_bounds

import config
import terrain as t

# ------------------------------------------------------------ thresholds
# A tile is "Mars-possible" only if it is bare and dry. Tune these with care
# and never just to pass a test: they are what we explain to the judges.
NDVI_MAX = 0.15          # median NDVI below this: little or no vegetation
WATER_MAX = 0.05         # under 5% of the tile is permanent water

# Three full years of MODIS, fixed so results are repeatable.
DATE_START = "2023-01-01"
DATE_END = "2026-01-01"

# Reference band for the within-world percentiles (THEMIS covers 60N-60S).
REF_LAT = 60.0
REF_SAMPLES_EARTH = 20000    # random points requested; ocean ones drop out
REF_BATCH = 4000             # points per Earth Engine request (limit 5000)
REF_SAMPLES_MARS = 300       # random tile-sized THEMIS windows
REF_SEED = 1

# Display labels from heat_rank, in thirds of each world's bare ground.
GROUND_LABELS = ("dusty", "sandy", "rocky")

TILE_M = t.TILE_PX * t.MARS_PIXEL_M     # one tile is about 9.3 km across

# ------------------------------------------------------------ Mars sources
THEMIS_NIGHT = ("/vsicurl/https://asc-pds-services.s3.us-west-2.amazonaws.com/"
                "wms_basemaps/Mars/THEMIS_ASU/"
                "Mars_MO_THEMIS-IR-Night_mosaic_60N60S_100m_v14_clon0.tif")
TES_ALBEDO = ("/vsicurl/https://planetarymaps.usgs.gov/mosaic/"
              "Mars_MGS_TES_Albedo_mosaic_global_7410m.tif")

# Stop GDAL listing remote folders before each open, which is slow.
GDAL_ENV = {"GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR"}


# =================================================================== Earth

def _earth_image(ee):
    """All Earth layers as one Earth Engine image: ndvi, water, ati, albedo."""
    def coll(asset):
        return ee.ImageCollection(asset).filterDate(DATE_START, DATE_END)

    ndvi = (coll("MODIS/061/MOD13A2").select("NDVI").median()
            .multiply(0.0001).rename("ndvi"))

    lst = coll("MODIS/061/MOD11A2")
    t_day = lst.select("LST_Day_1km").median().multiply(0.02)        # kelvin
    t_night = lst.select("LST_Night_1km").median().multiply(0.02)
    swing = t_day.subtract(t_night)

    albedo = (coll("MODIS/061/MCD43A3").select("Albedo_WSA_shortwave")
              .median().multiply(0.001).rename("albedo"))

    # A day-night swing under 1 K would blow the ratio up, so mask it.
    ati = (ee.Image(1).subtract(albedo)
           .divide(swing.updateMask(swing.gt(1))).rename("ati"))

    # JRC seasonality 12 means water in all twelve months: permanent water.
    water = (ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("seasonality")
             .eq(12).unmask(0).rename("water"))

    return ee.Image.cat([ndvi, water, ati, albedo])


def earth_layers(lat: float, lon: float, out_px: int = 240
                 ) -> dict[str, np.ndarray]:
    """Earth layers on exactly the grid terrain.earth_patch uses.

    Returns per-pixel ndvi, water (fraction), ati and albedo, each
    out_px x out_px, for the 1 degree tile holding (lat, lon). Missing pixels
    are NaN.
    """
    ee = config.init_ee()
    lat0, lon0 = math.floor(lat), math.floor(lon)
    step = 1.0 / out_px
    grid = ee.Projection("EPSG:4326", [step, 0, lon0, 0, -step, lat0 + 1])

    img = _earth_image(ee)
    # JRC is 30 m: average it down so each pixel holds a water fraction.
    water = (img.select("water")
             .reduceResolution(ee.Reducer.mean(), maxPixels=1024)
             .reproject(grid))
    rest = img.select(["ndvi", "ati", "albedo"]).reproject(grid)

    # Inset by half a pixel so the rectangle covers exactly out_px pixels.
    h = step / 2
    region = ee.Geometry.Rectangle([lon0 + h, lat0 + h, lon0 + 1 - h, lat0 + 1 - h],
                                   None, False)
    # toFloat: Earth Engine tracks each band's value range, and an NDVI band
    # would otherwise refuse -9999 as the fill value for missing pixels.
    props = (rest.addBands(water).toFloat()
             .sampleRectangle(region=region, defaultValue=-9999)
             .getInfo()["properties"])

    out = {}
    for name in ("ndvi", "water", "ati", "albedo"):
        arr = np.array(props[name], dtype="float32")
        arr[arr == -9999] = np.nan
        if arr.shape != (out_px, out_px):
            raise RuntimeError(f"{name} came back {arr.shape}, "
                               f"expected {(out_px, out_px)}")
        out[name] = arr
    return out


def mars_possible(cards: pd.DataFrame) -> pd.Series:
    """True where an Earth tile is bare and dry enough to stand in for Mars."""
    return (cards["ndvi"] < NDVI_MAX) & (cards["water"] < WATER_MAX)


def earth_reference() -> pd.DataFrame:
    """Earth's own distribution of ati and albedo, at tile scale.

    Random points between 60N and 60S, placed so every square kilometre is
    equally likely (the same arcsine trick as mars_reference). Ocean points
    have no MODIS land temperature and drop out, leaving land only. Each point
    also carries ndvi and water (1 if the point is permanent water), so
    bare_dry() can pick out the land that passes the Mars filter. Cached in
    data/processed/.
    """
    columns = ["ati", "albedo", "ndvi", "water"]
    path = config.PROCESSED / "earth_reference.parquet"
    if path.exists():
        cached = pd.read_parquet(path)
        if set(columns) <= set(cached.columns):
            return cached

    ee = config.init_ee()
    rng = np.random.default_rng(REF_SEED)
    s = math.sin(math.radians(REF_LAT))
    lats = np.degrees(np.arcsin(rng.uniform(-s, s, REF_SAMPLES_EARTH)))
    lons = rng.uniform(-180, 180, REF_SAMPLES_EARTH)
    image = _earth_image(ee).select(columns)

    # Earth Engine returns at most 5000 results per request, so ask in
    # batches small enough that even an all-land batch fits.
    rows = []
    for start in range(0, REF_SAMPLES_EARTH, REF_BATCH):
        points = ee.FeatureCollection([
            ee.Feature(ee.Geometry.Point([float(lo), float(la)]))
            for la, lo in zip(lats[start:start + REF_BATCH],
                              lons[start:start + REF_BATCH])])
        samples = image.sampleRegions(collection=points, scale=TILE_M,
                                      tileScale=4, geometries=False)
        rows += [f["properties"] for f in samples.getInfo()["features"]]
    ref = pd.DataFrame(rows, columns=columns)
    path.parent.mkdir(parents=True, exist_ok=True)
    ref.to_parquet(path)
    return ref


def bare_dry(ref: pd.DataFrame) -> pd.DataFrame:
    """The part of an Earth sample that would pass the Mars-possible filter."""
    return ref[(ref["ndvi"] < NDVI_MAX) & (ref["water"] < WATER_MAX)]


def ground_label(heat_rank) -> pd.Series:
    """Dusty, sandy or rocky, by which third of its world's ground it is in.

    For display only, never for matching.
    """
    bins = np.linspace(0, 1, len(GROUND_LABELS) + 1)
    return pd.cut(pd.Series(heat_rank), bins=bins, labels=GROUND_LABELS,
                  include_lowest=True)


# ==================================================================== Mars

def _radius(src) -> float:
    """Sphere radius the file's map projection uses (TES differs from MOLA)."""
    return CRS.from_wkt(src.crs.to_wkt()).ellipsoid.semi_major_metre


def mars_footprint(lat: float, lon: float, size_px: int = 400
                   ) -> tuple[float, float, float, float]:
    """The exact window terrain.mars_patch reads, as angles in radians.

    Returns (west, south, east, north). Angles, not metres, because each Mars
    map uses a slightly different sphere radius.
    """
    with rasterio.Env(**GDAL_ENV), rasterio.open(t.MOLA) as src:
        r = _radius(src)
        row, col = src.index(math.radians(lon) * r, math.radians(lat) * r)
        half = size_px // 2
        west, north = src.xy(row - half, col - half, offset="ul")
        east, south = src.xy(row - half + size_px, col - half + size_px,
                             offset="ul")
    return west / r, south / r, east / r, north / r


def _read_window(url: str, bounds_rad, out_px: int | None = None,
                 resampling=Resampling.nearest) -> np.ndarray:
    """Read one window of a Mars map given in radians. NaN where missing."""
    with rasterio.Env(**GDAL_ENV), rasterio.open(url) as src:
        r = _radius(src)
        west, south, east, north = (b * r for b in bounds_rad)
        win = from_bounds(west, south, east, north, src.transform)
        shape = None if out_px is None else (out_px, out_px)
        arr = src.read(1, window=win, out_shape=shape, resampling=resampling,
                       masked=True).astype("float32").filled(np.nan)
    return arr


def _to_grid(arr: np.ndarray, out_px: int) -> np.ndarray:
    """Pick out_px x out_px evenly spaced samples, keeping NaNs as NaN."""
    rows = ((np.arange(out_px) + 0.5) * arr.shape[0] / out_px).astype(int)
    cols = ((np.arange(out_px) + 0.5) * arr.shape[1] / out_px).astype(int)
    return arr[np.ix_(rows, cols)]


def mars_heat(lat: float, lon: float, size_px: int = 400) -> np.ndarray:
    """THEMIS night infrared on the same grid as terrain.mars_patch.

    Read at full 100 m resolution (the file has no overviews, so there is
    nothing cheaper), with 0 treated as a gap, then sampled down. About 3 MB.
    """
    arr = _read_window(THEMIS_NIGHT, mars_footprint(lat, lon, size_px))
    arr[arr == 0] = np.nan
    return _to_grid(arr, size_px)


def mars_albedo(lat: float, lon: float, size_px: int = 400) -> np.ndarray:
    """TES albedo on the same grid as terrain.mars_patch.

    TES pixels are 7.4 km, about one per tile, so this is a coarse layer.
    """
    return _read_window(TES_ALBEDO, mars_footprint(lat, lon, size_px),
                        out_px=size_px)


def mars_reference() -> pd.DataFrame:
    """Mars's own distribution of night infrared and albedo, at tile scale.

    THEMIS: REF_SAMPLES_MARS random tile-sized windows between 60N and 60S,
    placed so every square kilometre is equally likely.
    TES: the whole map is small, so every pixel in the band counts, weighted
    by its area (cos latitude). Cached in data/processed/.
    """
    path = config.PROCESSED / "mars_reference.parquet"
    if path.exists():
        return pd.read_parquet(path)

    rng = np.random.default_rng(REF_SEED)
    # Half a degree in from every edge, so no window hangs off the map.
    s = math.sin(math.radians(REF_LAT - 0.5))
    lats = np.degrees(np.arcsin(rng.uniform(-s, s, REF_SAMPLES_MARS)))
    lons = rng.uniform(-179.5, 179.5, REF_SAMPLES_MARS)

    heat = []
    with rasterio.Env(**GDAL_ENV), rasterio.open(THEMIS_NIGHT) as src:
        r = _radius(src)
        for la, lo in zip(lats, lons):
            x, y = math.radians(lo) * r, math.radians(la) * r
            half = TILE_M / 2
            win = from_bounds(x - half, y - half, x + half, y + half,
                              src.transform)
            block = src.read(1, window=win).astype("float32")
            block[block == 0] = np.nan
            if np.isfinite(block).any():
                heat.append(float(np.nanmean(block)))

    with rasterio.Env(**GDAL_ENV), rasterio.open(TES_ALBEDO) as src:
        tes = src.read(1, masked=True).astype("float32").filled(np.nan)
        rows = np.arange(src.height)
        row_lat = np.degrees(
            (src.transform.f + (rows + 0.5) * src.transform.e) / _radius(src))
    keep = np.abs(row_lat) <= REF_LAT
    vals = tes[keep]
    weights = np.repeat(np.cos(np.radians(row_lat[keep]))[:, None],
                        tes.shape[1], axis=1)
    ok = np.isfinite(vals)
    bright_q = _weighted_quantiles(vals[ok], weights[ok])

    heat_q = _weighted_quantiles(np.array(heat), np.ones(len(heat)))
    ref = pd.DataFrame({"heat": heat_q, "bright": bright_q})
    ref.attrs["themis_windows"] = len(heat)
    path.parent.mkdir(parents=True, exist_ok=True)
    ref.to_parquet(path)
    return ref


# ============================================================== percentiles

QUANTILES = np.linspace(0, 1, 1001)


def _weighted_quantiles(values: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """Values at QUANTILES of a weighted sample, smallest first."""
    order = np.argsort(values)
    v, w = values[order], weights[order]
    cum = (np.cumsum(w) - 0.5 * w) / w.sum()
    return np.interp(QUANTILES, cum, v)


def rank(values, reference) -> np.ndarray:
    """Percentile (0 to 1) of each value within a reference distribution.

    `reference` is either a raw sample or the quantile table from
    mars_reference(); both work because a sorted sample is its own quantile
    table.
    """
    ref = np.sort(np.asarray(reference, dtype="float64"))
    ref = ref[np.isfinite(ref)]
    q = np.linspace(0, 1, len(ref))
    return np.interp(np.asarray(values, dtype="float64"), ref, q)
