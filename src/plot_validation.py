"""Draw the validation charts: which Earth regions each Mars site matches.

Matches the style of figures/validation_elevation_only.png, so the charts
sit side by side in the presentation: one stacked bar per Mars site, one
colour per Earth region, the share written inside each bar.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # write files only; never open a window

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

COLOURS = {
    "Atacama": "#C65B3C",
    "Death Valley": "#D99B4F",
    "Black Desert": "#4E8FA8",
    "Nile Delta": "#6BA368",
}
LABEL_MIN = 0.05   # shares smaller than this are drawn but not labelled


def plot_shares(table: pd.DataFrame, title: str, caption: str, path) -> None:
    """Stacked horizontal bars. `table`: rows Mars sites, columns Earth regions,
    values shares from 0 to 1 that sum to 1 per row."""
    fig, ax = plt.subplots(figsize=(8.9, 4.5), dpi=200)
    sites = list(table.index)[::-1]          # first site on top
    for y, site in enumerate(sites):
        left = 0.0
        for region, colour in COLOURS.items():
            share = float(table.loc[site].get(region, 0.0))
            if share <= 0:
                continue
            ax.barh(y, share, left=left, height=0.78, color=colour,
                    edgecolor="white", linewidth=1)
            if share >= LABEL_MIN:
                ax.text(left + share / 2, y, f"{share:.0%}", ha="center",
                        va="center", color="white", fontsize=11,
                        fontweight="bold")
            left += share

    ax.set_yticks(range(len(sites)), sites, fontsize=11)
    ax.set_xlim(0, 1)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1],
                  ["0", "25%", "50%", "75%", "100%"], fontsize=10)
    ax.set_xlabel("Share of nearest Earth matches", fontsize=11)
    ax.tick_params(axis="y", length=0)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.set_title(title, fontsize=14, pad=14)

    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in COLOURS.values()]
    ax.legend(handles, COLOURS.keys(), loc="upper center", frameon=False,
              bbox_to_anchor=(0.5, -0.2), ncol=len(COLOURS), fontsize=11)
    fig.text(0.5, 0.02, caption, ha="center", va="bottom", fontsize=9,
             color="#666666", wrap=True)
    # Leave room on the left for the longest bar label.
    longest = max(len(str(label)) for label in sites)
    fig.subplots_adjust(left=min(0.3, 0.05 + 0.011 * longest), right=0.97,
                        top=0.88, bottom=0.33)
    fig.savefig(path)
    plt.close(fig)
