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


def main() -> None:
    earth_parts = []
    for name, (lat, lon) in EARTH_SITES.items():
        elev, px_x, px_y = t.earth_patch(lat, lon)
        cards = t.report_cards(elev, px_x, px_y)
        cards["region"] = name
        earth_parts.append(cards)
        print(f"{name:13s} {len(cards):5d} tiles   "
              f"mean slope {cards.mean_slope.mean():5.2f} deg   "
              f"relief {cards.relief.mean():6.1f} m")
    earth = pd.concat(earth_parts, ignore_index=True)

    mars_parts = []
    for name, (lat, lon) in MARS_SITES.items():
        cards = t.report_cards(t.mars_patch(lat, lon), t.MARS_PIXEL_M,
                               t.MARS_PIXEL_M)
        cards["site"] = name
        mars_parts.append(cards)
        print(f"{name:13s} {len(cards):5d} tiles   "
              f"mean slope {cards.mean_slope.mean():5.2f} deg   "
              f"relief {cards.relief.mean():6.1f} m")
    mars = pd.concat(mars_parts, ignore_index=True)

    # Put every feature on the same footing. Relief is measured in hundreds of
    # metres and slope in single degrees, so without this step relief alone
    # would decide every match.
    scaler = StandardScaler().fit(
        pd.concat([earth[t.FEATURES], mars[t.FEATURES]]))
    finder = NearestNeighbors(n_neighbors=NEIGHBOURS).fit(
        scaler.transform(earth[t.FEATURES]))
    _, idx = finder.kneighbors(scaler.transform(mars[t.FEATURES]))

    print("\nWhere Mars says it feels at home (all sites together)")
    votes = earth["region"].values[idx.ravel()]
    for region, share in pd.Series(votes).value_counts(normalize=True).items():
        print(f"  {region:13s} {share:5.1%}")

    print("\nPer Mars site")
    for name in MARS_SITES:
        rows = np.where(mars["site"].values == name)[0]
        v = pd.Series(earth["region"].values[idx[rows].ravel()])
        top = v.value_counts(normalize=True)
        print(f"  {name:11s} " + "  ".join(
            f"{r} {s:.0%}" for r, s in top.items()))


if __name__ == "__main__":
    main()
