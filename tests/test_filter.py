"""The Mars-possible filter, offline: bare, dry and, where known, not ice.

    pytest tests/test_filter.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import surface as s  # noqa: E402


def test_filter_without_ice_column_is_unchanged():
    """Grids built before the ice layer (Africa) keep their old answer."""
    cards = pd.DataFrame({"ndvi": [0.05, 0.30, 0.05], "water": [0.0, 0.0, 0.2]})
    assert s.mars_possible(cards).tolist() == [True, False, False]


def test_ice_over_half_the_tile_is_not_mars_possible():
    """Ice has NDVI near zero, like bare rock, so only the ice layer can
    stop a glacier being offered as a Mars twin."""
    cards = pd.DataFrame({"ndvi": [0.02, 0.02, 0.02, 0.02],
                          "water": [0.0, 0.0, 0.0, 0.0],
                          "ice": [0.92, 0.50, 0.49, None]})
    assert s.mars_possible(cards).tolist() == [False, False, True, True]
