"""Shared paths and Earth Engine setup.

Import from here rather than hardcoding paths, so the project works on
Windows, Linux and Colab without edits.

Earth Engine authenticates two different ways depending on where the code
runs, and `init_ee` picks the right one on its own:

  On a laptop   `earthengine authenticate` once, which drops a token in the
                user's home folder. Interactive, needs a browser.
  In the cloud  A service account key, read from the environment variable
                named in EE_KEY_ENV. No browser, so this is the only option
                in a headless container.

The key is a secret. It lives in the environment's settings, never in this
repository and never in a chat message.
"""

import base64
import json
import os
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

# Environment variable holding the service account key. Set it in the cloud
# environment's settings. Unset on a laptop, where interactive auth is used.
EE_KEY_ENV = "GEE_SERVICE_ACCOUNT_KEY"


def _is_readable_file(candidate):
    """True if `candidate` names a file we can read.

    A long base64 key is not a path, and asking the filesystem about one
    raises ENAMETOOLONG rather than answering False, so the question has to
    be asked defensively.
    """
    try:
        return Path(candidate).is_file()
    except (OSError, ValueError):
        return False


def _load_service_account_info():
    """Return the service account key as a dict, or None if none is set.

    Accepts the three shapes a secret store might hand us: a path to the
    JSON file, the raw JSON itself, or base64-encoded JSON for stores that
    mangle newlines.

    Errors never quote the value, so a broken key cannot leak into a log.
    """
    raw = os.environ.get(EE_KEY_ENV, "").strip()
    if not raw:
        return None

    if raw.startswith("{"):
        source = raw
    elif _is_readable_file(raw):
        source = Path(raw).read_text()
    else:
        try:
            source = base64.b64decode(raw, validate=True).decode()
        except Exception as exc:
            raise RuntimeError(
                f"{EE_KEY_ENV} is set but is not JSON, a readable file path, "
                f"or base64-encoded JSON."
            ) from exc

    try:
        info = json.loads(source)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{EE_KEY_ENV} did not parse as JSON.") from exc

    missing = {"client_email", "private_key"} - set(info)
    if missing:
        raise RuntimeError(
            f"{EE_KEY_ENV} is missing {sorted(missing)}. It should be the "
            f"whole service account JSON file, not one field from it."
        )
    return info


def init_ee(project=EE_PROJECT):
    """Initialize Earth Engine and return the `ee` module.

    Uses the service account when EE_KEY_ENV is set, otherwise falls back to
    the interactive credentials left by `earthengine authenticate`.
    """
    import ee

    info = _load_service_account_info()
    if info is None:
        ee.Initialize(project=project)
        return ee

    credentials = ee.ServiceAccountCredentials(
        info["client_email"], key_data=json.dumps(info)
    )
    ee.Initialize(credentials, project=project)
    return ee


def ee_auth_mode():
    """Describe how init_ee will authenticate, without touching the key.

    Safe to print. Returns a short string for diagnostics and notebooks.
    """
    info = _load_service_account_info()
    if info is None:
        return "interactive (run `earthengine authenticate` once)"
    return f"service account ({info['client_email']})"
