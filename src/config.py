"""Shared paths and Earth Engine setup.

Import from here rather than hardcoding paths, so the project works on
Windows, Linux and Colab without edits.
"""

from pathlib import Path

# Repository root, found relative to this file rather than the working
# directory, so notebooks and scripts both resolve it correctly.
ROOT = Path(__file__).resolve().parent.parent

DATA = ROOT / "data"
RAW = DATA / "raw"
PROCESSED = DATA / "processed"
NOTEBOOKS = ROOT / "notebooks"

# Earth Engine, Community tier. This is a project identifier, not a secret.
# Never attach a billing account to it.
EE_PROJECT = "rare-decker-493720-c2"


def init_ee():
    """Initialize Earth Engine against the project.

    Run `earthengine authenticate` once on a new machine first, otherwise
    this raises.
    """
    import ee

    ee.Initialize(project=EE_PROJECT)
    return ee
