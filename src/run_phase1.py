"""Run the first twin-finding test: does Mars ground look like desert ground?

Every Mars square votes for the Earth region holding its closest matches.
The Nile Delta is in the list on purpose, as a control. It is wet farmland,
so a sensible model should not choose it often.
"""

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

import terrain as t

MARS_SITES = {
    "Jezero":    (18.4, 77.5),
    "Gale":      (-5.4, 137.8),
    "Meridiani": (-2.0, -6.0),
}

EARTH_SITES = {
    "Atacama":      (-23.5, -69.5),   # known analog
    "Death Valley": (36.5, -117.5),   # known analog
    "Black Desert": (28.5, 28.5),     # our candidate, Egypt
    "Nile Delta":   (30.5, 31.5),     # control: should score low
}

NEIGHBOURS = 10


def _summary(name: str, cards: pd.DataFrame) -> None:
    print(f"{name:13s} {len(cards):5d} tiles   "
          f"mean slope {cards.mean_slope.mean():5.2f} deg   "
          f"relief {cards.relief.mean():6.1f} m")


def compare(verbose: bool = False):
    """Build every report card and find each Mars tile's nearest Earth tiles.

    Returns (earth, mars, idx): the two card tables, and for each Mars tile
    the row numbers of its NEIGHBOURS closest Earth tiles. Shared by main()
    and tests/test_validation.py so both judge the same comparison.
    """
    earth_parts = []
    for name, (lat, lon) in EARTH_SITES.items():
        elev, px_x, px_y = t.earth_patch(lat, lon)
        cards = t.report_cards(elev, px_x, px_y)
        cards["region"] = name
        earth_parts.append(cards)
        if verbose:
            _summary(name, cards)
    earth = pd.concat(earth_parts, ignore_index=True)

    mars_parts = []
    for name, (lat, lon) in MARS_SITES.items():
        cards = t.report_cards(t.mars_patch(lat, lon), t.MARS_PIXEL_M,
                               t.MARS_PIXEL_M)
        cards["site"] = name
        mars_parts.append(cards)
        if verbose:
            _summary(name, cards)
    mars = pd.concat(mars_parts, ignore_index=True)

    # Put every feature on the same footing. Relief is measured in hundreds of
    # metres and slope in single degrees, so without this step relief alone
    # would decide every match.
    scaler = StandardScaler().fit(
        pd.concat([earth[t.FEATURES], mars[t.FEATURES]]))
    finder = NearestNeighbors(n_neighbors=NEIGHBOURS).fit(
        scaler.transform(earth[t.FEATURES]))
    _, idx = finder.kneighbors(scaler.transform(mars[t.FEATURES]))
    return earth, mars, idx


def region_shares(earth: pd.DataFrame, idx: np.ndarray) -> pd.Series:
    """Fraction of all Mars matches that land in each Earth region."""
    votes = earth["region"].values[idx.ravel()]
    return pd.Series(votes).value_counts(normalize=True)


def main() -> None:
    earth, mars, idx = compare(verbose=True)

    print("\nWhere Mars says it feels at home (all sites together)")
    for region, share in region_shares(earth, idx).items():
        print(f"  {region:13s} {share:5.1%}")

    print("\nPer Mars site")
    table = {}
    for name in MARS_SITES:
        rows = np.where(mars["site"].values == name)[0]
        v = pd.Series(earth["region"].values[idx[rows].ravel()])
        top = v.value_counts(normalize=True)
        table[name] = top
        print(f"  {name:11s} " + "  ".join(
            f"{r} {s:.0%}" for r, s in top.items()))

    # Imported here so the tests, which only call compare(), need no plotting.
    import config
    import plot_validation
    chart = pd.DataFrame(table).T.reindex(columns=list(EARTH_SITES),
                                          fill_value=0.0).fillna(0.0)
    path = config.ROOT / "figures" / "validation_elevation_only.png"
    plot_validation.plot_shares(
        chart,
        title="Mars terrain matched against Earth, using elevation alone",
        caption=("Atacama and Death Valley are the analog sites NASA already "
                 "uses. The model was never told that.\nThe Nile Delta is a "
                 "control: wet farmland. It only scores on Meridiani, a flat "
                 "plain, which is why the Mars filter and albedo come next."),
        path=path)
    print(f"\nChart written to {path.relative_to(config.ROOT)}")


if __name__ == "__main__":
    main()
