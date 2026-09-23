"""Check that Earth Engine is reachable and authenticated.

Run it after setting up credentials on a new machine or in a new cloud
session:

    python src/check_ee.py

Deliberately cheap. It does one trivial server-side sum and one metadata
read, neither of which touches the monthly compute quota in any meaningful
way, so this is safe to run as often as needed.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config


def _hint(exc):
    """Map a startup failure to the fix, since the raw errors are opaque."""
    text = str(exc)

    if "_cffi_backend" in text or "cryptography" in text:
        return (
            "The installed cryptography package is broken, which breaks "
            "`import ee`. This shows up in fresh cloud containers where the "
            "system package ships without a working cffi backend. Fix:\n"
            "    pip install --ignore-installed cffi cryptography\n"
            "Plain --upgrade fails, because the system package has no RECORD "
            "file for pip to uninstall from."
        )

    if "serviceusage" in text or "does not have required permission" in text:
        return (
            "The key is valid but the service account lacks IAM permission "
            "to use the project. Grant it roles/serviceusage.serviceUsageConsumer "
            "in IAM & Admin, and check the project is registered for Earth "
            "Engine at https://code.earthengine.google.com/register"
        )

    if "No module named" in text:
        return "Missing dependency. Run: pip install earthengine-api"

    return (
        "If this says credentials are missing: on a laptop run "
        "`earthengine authenticate` once; in the cloud set the "
        f"{config.EE_KEY_ENV} environment variable in the environment's "
        "settings."
    )


def main():
    print(f"project   {config.EE_PROJECT}")
    print(f"auth      {config.ee_auth_mode()}")

    try:
        ee = config.init_ee()
    except Exception as exc:
        print(f"\nFAILED to initialize: {exc}")
        print("\n" + _hint(exc))
        return 1

    # Server-side arithmetic. Proves the round trip works at all.
    total = ee.Number(1).add(1).getInfo()
    if total != 2:
        print(f"\nFAILED: server returned {total} for 1 + 1")
        return 1
    print("round trip 1 + 1 = 2")

    # Metadata read, proving the project can actually see the catalogue.
    dem = ee.Image("USGS/SRTMGL1_003")
    scale = dem.projection().nominalScale().getInfo()
    print(f"catalogue  SRTM reachable, native scale {scale:.0f} m")

    print("\nEarth Engine is working.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
