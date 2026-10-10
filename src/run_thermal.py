"""Rerun the Phase 1 comparison with the Mars filter and albedo.

Same Mars sites, same Earth regions and same matching as run_phase1.py.

The chosen method is V1: terrain (slope, slope spread, relief) + the
Mars-possible filter + absolute albedo. Heat is not used for matching. The
other variants are kept so the history can be shown, each changing one thing:

  elevation only     Phase 1 (slope, slope spread, relief)
  + filter           green or wet Earth tiles dropped before matching
  percentile method  the first attempt, which failed: heat and brightness as
                     percentiles within each world, Earth ranked against all
                     land
  V1                 terrain + filter + absolute albedo  (the default)
  V2                 V1 + heat, Earth ranked against bare dry land only.
                     Experimental, shown only with --with-heat

Heat is still computed, to label Mars tiles dusty, sandy or rocky. Earth tiles
get no label: on Earth the heat measure mostly follows moisture.

    python src/run_thermal.py               V1 and its history
    python src/run_thermal.py --with-heat   also V2
"""

import argparse

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

import config
import plot_validation
import surface as s
import terrain as t
from run_phase1 import EARTH_SITES, MARS_SITES, NEIGHBOURS

DEFAULT = "V1"
FEATURES_V1 = t.FEATURES + ["albedo"]

VARIANTS = {
    "elevation only": (t.FEATURES, False),
    "+ filter": (t.FEATURES, True),
    "percentile method": (t.FEATURES + ["heat_rank_all", "bright_rank"], True),
    DEFAULT: (FEATURES_V1, True),
}
EXPERIMENTAL = {
    "V2": (FEATURES_V1 + ["heat_rank"], True),
}


def variants(with_heat: bool = False) -> dict:
    """The variants to run; V2 only when asked for."""
    return {**VARIANTS, **EXPERIMENTAL} if with_heat else dict(VARIANTS)


def build_cards(verbose: bool = False):
    """Report cards with surface layers for every Earth region and Mars site.

    Columns added on both worlds:
      albedo         absolute, 0 to 1
      heat_rank      percentile of heat within the world's bare dry ground
                     (used only by the experimental V2)
      heat_rank_all, bright_rank   the failed percentile method's features
    Earth also gets ndvi, water and mars_possible. Mars also gets ground:
    dusty, sandy or rocky, for display only. Earth gets no ground label.
    """
    earth_ref = s.earth_reference()
    earth_bare = s.bare_dry(earth_ref)
    mars_ref = s.mars_reference()
    if verbose:
        print(f"references: Earth {len(earth_ref)} land points, "
              f"{len(earth_bare)} of them bare and dry; "
              f"Mars {len(mars_ref)} quantiles")

    earth_parts = []
    for name, (lat, lon) in EARTH_SITES.items():
        elev, px_x, px_y = t.earth_patch(lat, lon)
        layers = s.earth_layers(lat, lon, out_px=elev.shape[0])
        cards = t.report_cards(elev, px_x, px_y, layers=layers)
        cards["heat_rank"] = s.rank(cards["ati"], earth_bare["ati"])
        cards["heat_rank_all"] = s.rank(cards["ati"], earth_ref["ati"])
        cards["bright_rank"] = s.rank(cards["albedo"], earth_ref["albedo"])
        cards["mars_possible"] = s.mars_possible(cards)
        cards["region"] = name
        earth_parts.append(cards)
    earth = pd.concat(earth_parts, ignore_index=True)

    mars_parts = []
    for name, (lat, lon) in MARS_SITES.items():
        layers = {"heat": s.mars_heat(lat, lon),
                  "albedo": s.mars_albedo(lat, lon)}
        cards = t.report_cards(t.mars_patch(lat, lon), t.MARS_PIXEL_M,
                               t.MARS_PIXEL_M, layers=layers)
        # All of Mars is bare and dry, so its reference is all of Mars.
        cards["heat_rank"] = s.rank(cards["heat"], mars_ref["heat"])
        cards["heat_rank_all"] = cards["heat_rank"]
        cards["bright_rank"] = s.rank(cards["albedo"], mars_ref["bright"])
        cards["site"] = name
        mars_parts.append(cards)
    mars = pd.concat(mars_parts, ignore_index=True)
    mars["ground"] = s.ground_label(mars["heat_rank"]).values

    if verbose:
        _describe(earth, "region")
        _describe(mars, "site")
    return earth, mars


def _describe(cards: pd.DataFrame, by: str) -> None:
    print()
    for name, g in cards.groupby(by, sort=False):
        line = f"{name:13s} {len(g):4d} tiles  albedo {g.albedo.median():.3f}"
        if "mars_possible" in g:
            line += (f"  ndvi {g.ndvi.median():.2f}"
                     f"  Mars-possible {int(g.mars_possible.sum()):3d}")
        if "ground" in g:
            ground = g["ground"].value_counts(normalize=True)
            line += "  " + " ".join(f"{k} {ground.get(k, 0):.0%}"
                                    for k in s.GROUND_LABELS)
        print(line)


def match(earth: pd.DataFrame, mars: pd.DataFrame, features: list[str],
          use_filter: bool) -> pd.DataFrame:
    """Each Mars tile's nearest Earth tiles. One row per vote, carrying the
    matched Earth tile's region and NDVI."""
    if use_filter:
        earth = earth[earth["mars_possible"]]
    earth = earth.dropna(subset=features).reset_index(drop=True)
    mars = mars.dropna(subset=features).reset_index(drop=True)

    scaler = StandardScaler().fit(pd.concat([earth[features], mars[features]]))
    finder = NearestNeighbors(n_neighbors=NEIGHBOURS).fit(
        scaler.transform(earth[features]))
    _, idx = finder.kneighbors(scaler.transform(mars[features]))
    picked = earth.iloc[idx.ravel()]
    return pd.DataFrame({
        "site": np.repeat(mars["site"].values, NEIGHBOURS),
        "region": picked["region"].values,
        "ndvi": picked["ndvi"].values,
    })


def shares(votes: pd.DataFrame) -> pd.Series:
    """Fraction of all Mars matches that land in each Earth region."""
    out = votes["region"].value_counts(normalize=True)
    return out.reindex(list(EARTH_SITES), fill_value=0.0)


def per_site(votes: pd.DataFrame) -> pd.DataFrame:
    """Rows are Mars sites, columns are Earth regions, values are shares."""
    table = pd.crosstab(votes["site"], votes["region"], normalize="index")
    return table.reindex(index=list(MARS_SITES), columns=list(EARTH_SITES),
                         fill_value=0.0)


def all_votes(earth, mars, with_heat: bool = False) -> dict[str, pd.DataFrame]:
    return {name: match(earth, mars, f, flt)
            for name, (f, flt) in variants(with_heat).items()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--with-heat", action="store_true",
                        help="also run the experimental V2 (V1 + heat)")
    args = parser.parse_args()

    earth, mars = build_cards(verbose=True)
    runs = variants(args.with_heat)
    votes = all_votes(earth, mars, args.with_heat)

    table = pd.DataFrame({name: shares(v) for name, v in votes.items()})
    print("\nShare of all Mars matches, by Earth region (%)")
    print((table * 100).round(1).to_string())
    known = table.loc[["Atacama", "Death Valley"]].sum()
    print("\nAtacama + Death Valley (%)")
    print((known * 100).round(1).to_string())

    for name in [DEFAULT] + list(EXPERIMENTAL if args.with_heat else []):
        print(f"\nPer Mars site, {name} (%)")
        print((per_site(votes[name]) * 100).round(0).astype(int).to_string())

    nile = earth[earth["region"] == "Nile Delta"]
    removed = 1 - nile["mars_possible"].mean()
    print(f"\nFilter removes {removed:.0%} of the Nile Delta box's tiles")
    worst = max(float(v["ndvi"].max()) for k, v in votes.items() if runs[k][1])
    print(f"Highest NDVI of any matched tile, filtered variants: {worst:.4f} "
          f"(must be below {s.NDVI_MAX})")

    chart = table[["elevation only", "+ filter", "percentile method", "V1"]].T
    chart.index = ["Elevation only", "+ Mars filter", "Percentile method",
                   "V1: + albedo"]
    nile_pct = table.loc["Nile Delta", "percentile method"]
    path = config.ROOT / "figures" / "validation_with_heat.png"
    plot_validation.plot_shares(
        chart,
        title="What we tried: all Mars sites matched against Earth",
        caption=("The percentile method ranked heat and brightness within each "
                 f"world and failed: the Nile Delta box rose to {nile_pct:.0%}.\n"
                 "V1 compares absolute albedo instead and drops heat from "
                 "matching. The Nile Delta box also holds desert east of Cairo."),
        path=path)
    print(f"\nChart written to {path.relative_to(config.ROOT)}")


if __name__ == "__main__":
    main()
