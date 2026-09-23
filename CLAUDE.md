# CLAUDE.md

Instructions for Claude Code sessions on this repository, on any team laptop or
in the cloud. Local Claude memory does not travel between machines, so anything
a future session needs belongs here.

## The project

Planetary Twin Finder: finds places on Earth whose terrain best matches proposed
landing and base sites on the Moon and Mars, for NASA Space Apps Challenge 2026
(hackathon 14 to 15 November 2026). **Read `HANDOFF.md` for the full picture:**
features, data sources, build order, accounts and open decisions.

## Rules we work by

- **Quote every path.** The project folder name has spaces
  (`Nasa Space Apps 2026` on Marwan's laptop).
- **Never commit keys or data.** No API keys, passwords, tokens or service
  account JSON in any file or commit, and never ask anyone to paste one into a
  file or the chat. `.gitignore` already covers `data/`, rasters (`*.tif`,
  `*.nc`, ...), `.env`, `keys.txt`, `*.key` and service account `*.json`. Only
  the `.gitkeep` files under `data/` are tracked.
- **Verify installer fingerprints.** Check the SHA256 of any installer against
  what the publisher lists before running it. Download only from the official
  source.
- **Explain, then wait.** Explain each command in plain language before running
  it and wait for approval. If a command fails, show the error and explain it
  before trying a fix. Don't stage, commit or push unless asked.
- **Read code before running it.** A judge may ask how it works.

## Setup

```bash
conda env create -f environment.yml    # portable: Mac, Linux, Windows
conda activate analog
earthengine authenticate               # once per laptop, opens a browser
python src/check_ee.py                 # confirms Earth Engine works
```

- `environment.yml` lists only the requested packages, unpinned (Python 3.11,
  conda-forge only). `environment-lock.yml` is the exact Windows (win-64) build
  of Marwan's environment, for `conda env create -f environment-lock.yml` if an
  exact rebuild is ever needed. It does not work on Mac or Linux.
- Solving takes 5 to 15 minutes. That is normal; check the CPU is busy before
  calling it stuck.
- If 3.11 ever refuses to solve, use Python 3.12. Not 3.13 or 3.14.
- Cloud containers can't run `earthengine authenticate`; they use the
  `GEE_SERVICE_ACCOUNT_KEY` environment variable instead. See `README.md` and
  `src/config.py`.

## Earth Engine

Project ID: `rare-decker-493720-c2` (an identifier, not a secret). Community
tier: no billing account, ever. Keep jobs coarse and regional so the quota
lasts. In code, don't hardcode the ID; use `src/config.py`:

```python
from config import init_ee   # with src/ on the path
ee = init_ee()               # project rare-decker-493720-c2
```

## Known issues

- **Smart App Control (Windows 11) must be off.** When it is on, it blocks
  unsigned compiled Python files at random, for example
  `ImportError: DLL load failed ... An Application Control policy has blocked
  this file` from pandas. Reinstalling does not help. The user turns it off
  themselves: Windows Security, App & browser control, Smart App Control. On
  many builds it cannot be turned back on without resetting Windows, so read
  the warning first. Check its state read-only with
  `(Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\CI\Policy").VerifiedAndReputablePolicyState`,
  where 0 means Off.
- **Flaky connections break big conda downloads.** The 109 MB `mkl` package
  is the one that failed. Raise conda's retries on the machine:
  `conda config --set remote_max_retries 6`, then
  `remote_read_timeout_secs 120` and `remote_connect_timeout_secs 60`.
  Already-downloaded packages are reused on retry. If `mkl` keeps failing,
  `nomkl` is the fallback, but ask first.
- **conda channels.** Miniforge ships a `mirrored_channels` entry that also
  lets it fetch conda-forge from `prefix.dev`. That is kept on purpose.
  `conda config --show-sources` does not display it, so print the raw
  `.condarc` files when auditing channels.
- **Regenerating the environment files** (conda 26):
  `conda env export -n analog --from-history --file environment.yml`, and
  `conda export -n analog --format=environment-yaml --file environment-lock.yml`.
  The second needs `--format` because conda picks the format from the file
  name. Delete the `prefix:` line from both, since it holds a personal path.
- **Windows PowerShell 5.1 pitfalls:**
  - `>` writes UTF-16, which YAML tools may reject. Use a tool's own
    `--file` option.
  - `powershell -Command "..."` strips inner double quotes. Use `-File` with a
    script.
  - `git commit -F -` does not read a here-string passed as an argument. Write
    the message to a file.
  - `Invoke-WebRequest` stalls on large downloads. Use `curl.exe -L --fail`.

## Machine-specific: Marwan's laptop only

- **`C:\` is a stray git repository** (an old Flutter checkout, thousands of
  files showing as deleted). Leave it completely alone: don't run git against
  it, don't commit, don't delete `C:\.git`. Always run git from inside the
  project folder or with `git -C "<project folder>"`. Other laptops don't have
  this.
- Project folder: `C:\Users\Marwan\Desktop\Nasa Space Apps 2026`
- Miniforge 26.7.2 at `C:\Users\Marwan\miniforge3` (user install, not on PATH),
  with retry settings in `C:\Users\Marwan\.condarc`. System Python 3.14 is
  separate and left untouched.
- Smart App Control turned off on 2026-09-23.

## Where we are

*Update this section whenever the status changes.*

As of 2026-09-23, setup is done and Phase 1 hasn't started.

- **Done:** the `analog` environment is built on Marwan's laptop and every
  import passes: Python 3.11.16, GDAL 3.12.3, rasterio 1.4.4, geopandas 1.1.4,
  scikit-learn 1.9.1. The repo has its structure, both environment files and
  `HANDOFF.md`. Earth Engine auth code (`src/config.py`, `src/check_ee.py`) was
  merged in PR #1.
- **Not done:** `earthengine authenticate` on Marwan's laptop (no credentials
  yet); inviting the remaining teammates. `HANDOFF.md` section 6 is out of
  date: it still calls the environment "in progress".
- **Next:** Phase 1 of the build order in `HANDOFF.md`. Build a small
  elevation-only test on coarse grids, including the Nile Delta control, then
  run the validation test.
