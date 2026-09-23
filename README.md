# analog-finder
Finding places on Earth that match the ground on the Moon and Mars. NASA Space Apps 2026.

## Setup

Rebuild the Python environment:

```bash
conda env create -f environment.yml
conda activate analog
```

Check Earth Engine works:

```bash
python src/check_ee.py
```

On a laptop, run `earthengine authenticate` once first. In a cloud container
there is no browser, so set `GEE_SERVICE_ACCOUNT_KEY` to a service account key
instead; `src/config.py` picks whichever is available.

Fresh cloud containers need two extra steps, because the preinstalled
`cryptography` is broken in a way that stops `import ee`:

```bash
pip install --ignore-installed cffi cryptography
pip install earthengine-api
```

`check_ee.py` recognises both failures and prints the fix.
