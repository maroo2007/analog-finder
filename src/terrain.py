"""Phase 1: compare the shape of the ground on Mars with the shape of the ground on Earth.

Nothing here needs an account or an API key. All data sources are open:
  Mars  - MOLA global elevation, 463 m per pixel, USGS Astropedia (public domain)
  Moon  - LOLA south pole elevation, 80 m per pixel, NASA PGDA (80 S to the pole)
  Earth - Copernicus DEM 30 m, 1 degree tiles, AWS Open Data

Both are read straight from the internet with GDAL's /vsicurl, so only the small
window we ask for is downloaded. Nothing is saved to disk.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import rasterio
from rasterio.enums import Resampling
from rasterio.windows import Window

# Mars
MOLA = ("/vsicurl/https://planetarymaps.usgs.gov/mosaic/"
        "Mars_MGS_MOLA_DEM_mosaic_global_463m.tif")
MARS_RADIUS_M = 3396190.0
MARS_PIXEL_M = 463.0

# Earth
COP_BASE = "https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com"
EARTH_PIXEL_DEG = 1.0 / 3600.0      # 1 arc second
EARTH_METRES_PER_DEG = 111320.0

# One tile is this many pixels across, on both worlds, after Earth is coarsened.
TILE_PX = 20


# ---------------------------------------------------------------- Mars

def mars_patch(lat: float, lon: float, size_px: int = 400) -> np.ndarray:
    """Cut a square of Martian ground centred on a latitude and longitude.

    The MOLA map is an equirectangular projection measured in metres, so a
    latitude and longitude has to be turned into metres before asking for a
    pixel. Doing that by hand, rather than assuming the map is a plain
    lat/lon grid, is what keeps the squares in the right place.
    """
    x = math.radians(lon) * MARS_RADIUS_M
    y = math.radians(lat) * MARS_RADIUS_M
    with rasterio.open(MOLA) as src:
        row, col = src.index(x, y)
        half = size_px // 2
        window = Window(col - half, row - half, size_px, size_px)
        return src.read(1, window=window).astype("float32")


# ---------------------------------------------------------------- Moon

# LOLA south pole DEM from NASA PGDA (Barker et al. 2023, PSJ 4, 183;
# doi:10.60903/gsfcpgda-lola-spole): 80 S to the pole, 80 m pixels, polar
# stereographic on a 1,737,400 m sphere with true scale at the pole. A
# cloud-optimized GeoTIFF, so only the window we ask for is downloaded.
# Every Artemis region is south of 80 S, where an equirectangular map is
# badly stretched, which is why this map is used instead of the global LDEM.
MOON_SOUTH_DEM = ("/vsicurl/https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/"
                  "LDEM_80S_80MPP_ADJ.TIF")
MOON_RADIUS_M = 1737400.0
MOON_PIXEL_M = 463.0          # the same ground pixel as Mars and Earth
MOON_SOUTH_LIMIT = -80.0


def moon_xy(lat: float, lon: float) -> tuple[float, float]:
    """Latitude and longitude to the DEM's south polar stereographic metres.

    rho is the distance from the pole on the map. x points to longitude 90 E
    and y to longitude 0, the convention of the PGDA south pole products.
    """
    rho = 2 * MOON_RADIUS_M * math.tan(math.pi / 4 + math.radians(lat) / 2)
    return rho * math.sin(math.radians(lon)), rho * math.cos(math.radians(lon))


def moon_scale(lat: float) -> float:
    """How much the map stretches distances at a latitude (1 at the pole).
    At 84 S a map metre is 0.3% shorter on the ground than it looks."""
    return 2 / (1 + math.sin(math.radians(-lat)))


def moon_patch(lat: float, lon: float, size_px: int = 120) -> np.ndarray:
    """Cut a square of lunar ground near the south pole, 463 m per pixel.

    The DEM's 80 m pixels are averaged to 463 m (Resampling.average), as
    MOLA's pixels are averages and Earth is averaged the same way, so a tile
    is the same 20 x 20 pixels, about 9.3 km, on all three worlds. The pixel
    size on the map is stretched by moon_scale so it is 463 m on the ground.
    The square is aligned with the map, not with north; slope, roughness and
    relief do not depend on direction.
    """
    if lat > MOON_SOUTH_LIMIT:
        raise ValueError(f"latitude {lat} is north of the south pole DEM "
                         f"({MOON_SOUTH_LIMIT})")
    x, y = moon_xy(lat, lon)
    half = size_px * MOON_PIXEL_M * moon_scale(lat) / 2
    # PGDA sometimes answers a block request with 0 bytes; retrying fixes it.
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
                      GDAL_HTTP_MAX_RETRY=3, GDAL_HTTP_RETRY_DELAY=2):
        with rasterio.open(MOON_SOUTH_DEM) as src:
            window = src.window(x - half, y - half, x + half, y + half)
            return src.read(1, window=window, out_shape=(size_px, size_px),
                            resampling=Resampling.average).astype("float32")


# ---------------------------------------------------------------- Earth

def _cop_tile_name(lat_floor: int, lon_floor: int) -> str:
    ns = f"{'N' if lat_floor >= 0 else 'S'}{abs(lat_floor):02d}"
    ew = f"{'E' if lon_floor >= 0 else 'W'}{abs(lon_floor):03d}"
    return f"Copernicus_DSM_COG_10_{ns}_00_{ew}_00_DEM"


def earth_patch(lat: float, lon: float, out_px: int = 240
                ) -> tuple[np.ndarray, float, float]:
    """Read one Copernicus tile, coarsened to roughly Mars's pixel size.

    Returns the heights plus how many metres one pixel covers east-west and
    north-south. Those two numbers differ away from the equator, because lines
    of longitude crowd together towards the poles, and slope is wrong if you
    ignore it.
    """
    lat_floor, lon_floor = math.floor(lat), math.floor(lon)
    name = _cop_tile_name(lat_floor, lon_floor)
    url = f"/vsicurl/{COP_BASE}/{name}/{name}.tif"
    with rasterio.open(url) as src:
        # out_shape makes GDAL read a decimated copy from the file's own
        # overviews, so a 240 x 240 request does not download 25 MB.
        # Average, not the default nearest neighbour: MOLA's 463 m pixels are
        # averages of the original shots, and nearest neighbour made Earth
        # look rougher (slope spread 6 to 9% high). Averaging the overviews
        # lands within 1 to 3% of averaging the full 30 m data, 20x faster.
        elev = src.read(1, out_shape=(out_px, out_px), masked=True,
                        resampling=Resampling.average
                        ).astype("float32").filled(np.nan)

    centre_lat = lat_floor + 0.5
    deg_per_px = 1.0 / out_px
    px_y_m = deg_per_px * EARTH_METRES_PER_DEG
    px_x_m = px_y_m * math.cos(math.radians(centre_lat))
    return elev, px_x_m, px_y_m


# ------------------------------------------------------- the report cards

def report_cards(elev: np.ndarray, px_x_m: float, px_y_m: float,
                 tile: int = TILE_PX,
                 layers: dict[str, np.ndarray] | None = None) -> pd.DataFrame:
    """Describe every small square of ground with the same three numbers.

    mean_slope    how steep it is on average, in degrees
    slope_spread  whether the steepness is even or a mix of flat and steep
    relief        the height difference between the lowest and highest point

    `layers` adds more per-pixel maps on the same grid as `elev`, for example
    heat and brightness from src/surface.py. Each becomes a column holding the
    tile's mean, ignoring missing pixels. `row` and `col` give the tile's
    top-left pixel, so tiles can be matched back to places.
    """
    gy, gx = np.gradient(elev, px_y_m, px_x_m)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    layers = layers or {}
    for name, arr in layers.items():
        if arr.shape != elev.shape:
            raise ValueError(f"layer {name} is {arr.shape}, elev is {elev.shape}")

    rows = []
    for r in range(0, elev.shape[0] - tile + 1, tile):
        for c in range(0, elev.shape[1] - tile + 1, tile):
            e = elev[r:r + tile, c:c + tile]
            s = slope[r:r + tile, c:c + tile]
            if np.isnan(e).any():
                continue
            card = {
                "row": r,
                "col": c,
                "mean_slope": float(s.mean()),
                "slope_spread": float(s.std()),
                "relief": float(e.max() - e.min()),
            }
            for name, arr in layers.items():
                block = arr[r:r + tile, c:c + tile]
                card[name] = (float(np.nanmean(block))
                              if np.isfinite(block).any() else np.nan)
            rows.append(card)
    return pd.DataFrame(rows)


FEATURES = ["mean_slope", "slope_spread", "relief"]
