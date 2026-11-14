"""Diviner temperatures for the nine Artemis regions: context, not matching.

The challenge's resource list points to LRO Diviner for the poles. Diviner
is a thermal radiometer: it measures how warm the ground gets, which no
place on Earth can copy, so it is shown beside the Moon twins ("what Earth
can't copy") and never used to rank them.

Source: the Diviner Polar Resource Product, south (Paige et al. 2010,
Science 330, 479, doi:10.1126/science.1187726), on the PDS Geosciences node:

  urn-nasa-pds-lro_diviner_derived1/data_derived_prp/dlre_prp_south.tab
  (+ dlre_prp_south.xml, the PDS4 label)

It is 2,880,000 triangles of a Kaguya laser-altimeter mesh, grid cells
about 500 m across (two triangles each), in a 600 km square around the south pole (to 80 S, 75.9 S
at the corners). Each triangle has its annual maximum surface temperature,
its annual average temperature 2 cm below the surface, and the depth below
which water ice would be stable (0 = at the surface, -999 = not within
2.87 m).

For each region this takes the triangles whose centre lies inside the
region's outline (tested in south polar stereographic coordinates, the same
map as terrain.moon_xy, so longitudes near the pole do not distort the
outline), weights them by their area and writes
data/processed/moon_diviner.json, which build_web_data.py adds to
targets.json as each Moon target's "diviner" object.

Cold trap: annual maximum surface temperature below 110 K, cold enough for
surface water ice to survive for billions of years (Paige et al. 2010).
That is a temperature test, not permanent shadow: Diviner measures heat,
not light. The product has no minimum (the coldest winter night).

    python src/run_diviner.py
"""

from __future__ import annotations

import hashlib
import json
import sys

import numpy as np
import pandas as pd
import shapely

import config
import run_moon_targets
import terrain as t

PDS = ("https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/"
       "data_derived_prp/")
TABLE = config.ROOT / "data" / "raw" / "diviner" / "dlre_prp_south.tab"
CACHE = config.PROCESSED / "diviner_prp_south.parquet"
OUT = config.PROCESSED / "moon_diviner.json"
# MD5 of dlre_prp_south.tab in the bundle's checksum manifest,
# urn-nasa-pds-lro_diviner_derived1.md5 (checked by md5_ok below).
MD5 = "80cdfe83592a3419c74b1b55b636711e"
COLD_TRAP_K = 110.0             # Paige et al. 2010
ICE_NOT_NEAR = -999.0           # label: ice not stable within 2.8738 m
KELVIN = 273.15
SOURCE = ("LRO Diviner Polar Resource Product, south (Paige et al. 2010, "
          "Science 330, 479, doi:10.1126/science.1187726), PDS Geosciences "
          "node, bundle urn:nasa:pds:lro_diviner_derived1")
NOTE = ("Context, not used for matching. Cold trap: annual maximum surface "
        "temperature below 110 K, where surface water ice can survive "
        "(Paige et al. 2010); a temperature test, not permanent shadow. "
        "The product has no winter minimum.")

COLUMNS = ["tri1_x", "tri1_y", "tri1_z", "tri2_x", "tri2_y", "tri2_z",
           "tri3_x", "tri3_y", "tri3_z", "tri_clon", "tri_clat", "tri_calt",
           "temp_avg", "temp_max", "ice_depth"]


def load() -> pd.DataFrame:
    """The PRP table, with each triangle's area in km2 (read once, then cached)."""
    if CACHE.exists():
        return pd.read_parquet(CACHE)
    # Fixed-width fields, separated by a comma and padding spaces.
    df = pd.read_csv(TABLE, sep=",", skipinitialspace=True, skiprows=1,
                     header=None, names=COLUMNS, engine="c", dtype=np.float64)
    v = [df[[f"tri{i}_x", f"tri{i}_y", f"tri{i}_z"]].to_numpy() for i in (1, 2, 3)]
    df["area_km2"] = 0.5 * np.linalg.norm(np.cross(v[1] - v[0], v[2] - v[0]), axis=1)
    keep = ["tri_clon", "tri_clat", "temp_avg", "temp_max", "ice_depth", "area_km2"]
    df = df[keep]
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(CACHE)
    return df


def stereo_xy(lat, lon):
    """terrain.moon_xy for arrays."""
    rho = 2 * t.MOON_RADIUS_M * np.tan(np.pi / 4 + np.radians(lat) / 2)
    return rho * np.sin(np.radians(lon)), rho * np.cos(np.radians(lon))


def inside(region: dict, lat, lon) -> np.ndarray:
    ring = [t.moon_xy(la, lo) for lo, la in region["outline"]]
    x, y = stereo_xy(lat, lon)
    return shapely.contains_xy(shapely.Polygon(ring), x, y)


def _temps(k: dict) -> dict:
    """The same numbers in kelvin and Celsius, one decimal."""
    return {"k": {n: round(v, 1) for n, v in k.items()},
            "c": {n: round(v - KELVIN, 1) for n, v in k.items()}}


def summarise(tri: pd.DataFrame) -> dict:
    w = tri["area_km2"].to_numpy()
    share = lambda m: round(float(w[m].sum() / w.sum()), 4)   # noqa: E731
    tmax, tavg, ice = (tri[c].to_numpy() for c in ("temp_max", "temp_avg", "ice_depth"))
    return {
        "annual_max_surface": _temps({"lowest": float(tmax.min()),
                                      "mean": float(np.average(tmax, weights=w)),
                                      "highest": float(tmax.max())}),
        "annual_mean_2cm": _temps({"lowest": float(tavg.min()),
                                   "mean": float(np.average(tavg, weights=w)),
                                   "highest": float(tavg.max())}),
        "cold_trap_share": share(tmax < COLD_TRAP_K),
        "ice_stable_surface_share": share(ice == 0),
        "ice_stable_within_2_9m_share": share(ice != ICE_NOT_NEAR),
        "triangles": int(len(tri)),
        "area_km2": round(float(w.sum()), 1),
    }


def md5_ok() -> str:
    h = hashlib.md5()
    with open(TABLE, "rb") as f:
        for block in iter(lambda: f.read(1 << 22), b""):
            h.update(block)
    got = h.hexdigest()
    if MD5 and got != MD5:
        raise SystemExit(f"MD5 mismatch: {got} != {MD5} (download again)")
    return got


def main() -> int:
    md5 = md5_ok()
    df = load()
    # Two triangles per grid cell, so a cell side is sqrt(2 x triangle area).
    spacing_m = round(float(np.sqrt(2 * df["area_km2"].median())) * 1000)
    out = {"source": SOURCE, "note": NOTE,
           "files": [PDS + "dlre_prp_south.tab", PDS + "dlre_prp_south.xml"],
           "md5": md5, "grid_spacing_m": spacing_m,
           "cold_trap_k": COLD_TRAP_K, "regions": {}}
    lat, lon = df["tri_clat"].to_numpy(), df["tri_clon"].to_numpy()
    for r in run_moon_targets.load_regions():
        s = summarise(df[inside(r, lat, lon)])
        out["regions"][r["id"]] = s
        m = s["annual_max_surface"]["k"]
        print(f"{r['id']:20s} {s['triangles']:6d} tri, {s['area_km2']:7.1f} km2 "
              f"(NASA {r['area_km2']}), max {m['lowest']:.0f}-{m['highest']:.0f} K, "
              f"mean {s['annual_mean_2cm']['k']['mean']:.0f} K, "
              f"cold trap {s['cold_trap_share']:.1%}, "
              f"surface ice {s['ice_stable_surface_share']:.1%}", flush=True)
    OUT.write_text(json.dumps(out, indent=1))
    print(f"grid spacing {spacing_m} m; wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
