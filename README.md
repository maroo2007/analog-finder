# analog-finder
Finding places on Earth that match the ground on the Moon and Mars. NASA Space Apps 2026.

## Setup

Mac and Linux: use `environment.yml`. Windows: `environment-lock.yml`
reproduces the exact build.

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

## Daily workflow

Every time you start working (Windows PowerShell shown; quote the path, it has
spaces):

```powershell
conda activate analog
cd "C:\Users\Marwan\Desktop\Nasa Space Apps 2026"   # your own clone's folder
git pull
jupyter lab
```

JupyterLab opens in your browser. Stop it with Ctrl+C in the terminal, then
`git push` your work.

## Team workflow

- Run `git pull` before you start work.
- Run `git push` when you're done.
- For bigger changes, work on your own branch (one per person) and open a pull
  request.
- Never commit anything in `data/`, or any key, password or service account
  file.

Setting up a new laptop:

```bash
git clone https://github.com/maroo2007/analog-finder
cd analog-finder
conda env create -f environment.yml
conda activate analog
earthengine authenticate
```

On Windows 11, turn off Smart App Control first, or it blocks parts of pandas
and other compiled libraries. See `CLAUDE.md`.
