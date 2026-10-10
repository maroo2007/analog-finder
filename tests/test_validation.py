"""Known-answer tests that protect the science as the code grows.

They read live data over the internet (MOLA and Copernicus DEM, no key), so
they are marked `network`. The Phase 1 comparison takes about 4 minutes, so
it is also marked `slow`. Run from the repo root:

    pytest -m network                  everything, before merging
    pytest -m "network and not slow"   quick day-to-day check
    pytest -m "not network"            offline
"""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import run_phase1  # noqa: E402
import terrain as t  # noqa: E402

# Olympus Mons caldera, and the middle of Jezero crater's floor.
OLYMPUS_MONS = (18.65, -133.8)
JEZERO_FLOOR = (18.38, 77.58)


@pytest.mark.network
def test_olympus_mons_summit_height():
    """If the coordinates or the map projection were wrong, the tallest
    volcano in the solar system would not show up at the right height."""
    patch = t.mars_patch(*OLYMPUS_MONS, size_px=300)
    summit = float(np.nanmax(patch))
    assert 20_500 <= summit <= 22_000, f"summit {summit:.0f} m"


@pytest.mark.network
def test_jezero_crater_floor_is_deep():
    """Jezero's floor, where Perseverance landed, sits about 2.6 km below the
    Mars datum. A median over a small central patch ignores stray hills."""
    patch = t.mars_patch(*JEZERO_FLOOR, size_px=30)
    floor = float(np.nanmedian(patch))
    assert floor < -2_000, f"floor {floor:.0f} m"


@pytest.fixture(scope="module")
def phase1_shares():
    earth, _, idx = run_phase1.compare()
    return run_phase1.region_shares(earth, idx)


@pytest.mark.network
@pytest.mark.slow
def test_known_analogs_win_phase1(phase1_shares):
    """The validation test: without being told, the model should send most
    Mars matches to the analog sites NASA already uses."""
    known = phase1_shares.get("Atacama", 0) + phase1_shares.get("Death Valley", 0)
    assert known >= 0.60, f"Atacama + Death Valley = {known:.1%}"


@pytest.mark.network
@pytest.mark.skip(reason="needs thermal data (ENGINE_PROMPTS.md prompt 1)")
def test_nile_delta_rejected_with_thermal(phase1_shares):
    """Wet farmland should stop matching Mars once heat and brightness are
    features. Elevation alone gives it about 13%."""
    assert phase1_shares.get("Nile Delta", 0) < 0.05
