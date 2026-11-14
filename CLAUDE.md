# CLAUDE.md

Instructions for Claude Code sessions on this repository, on any team laptop or
in the cloud. Local Claude memory does not travel between machines, so anything
a future session needs belongs here.

## The project

Planetary Twin Finder: finds places on Earth whose terrain best matches proposed
landing and base sites on the Moon and Mars, for NASA Space Apps Challenge 2026
(hackathon 14 to 15 November 2026). **Read `HANDOFF.md` for the full picture:**
status, method, targets, data sources, the website plan, submission rules,
accounts, open decisions and history.

## Rules we work by

- **Fetch before starting work.** Several people push from different laptops
  and from Claude Code cloud sessions. Run `git fetch origin` and
  `git status --short --branch` first. If `main` is behind, read what changed
  (`git log main..origin/main`, `git diff main origin/main`) before editing
  anything, then `git pull --ff-only`. On 2026-09-23 this caught 8 commits
  nobody on the laptop knew about.
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
- **Every Earth Engine task gets a cost cap.** Run batch exports through
  `earth_grid.run_capped`, which polls every 10 seconds and cancels the task
  the moment its compute passes the cap. Estimate from a realistic test area
  (one country, with coast and sea), never from a tiny all-land square: on
  2026-10-10 an uncapped Africa export estimated at 5 EECU-hours burned 14.7
  before it was cancelled by hand. The Community tier gives 150 EECU-hours a
  month (resets on the 1st); the team budget for October is 60.

## Setup

```bash
conda env create -f environment.yml    # portable: Mac, Linux, Windows
conda activate analog
earthengine authenticate               # once per laptop, opens a browser
python src/check_ee.py                 # confirms Earth Engine works
```

- `environment.yml` lists only the requested packages, unpinned (Python 3.11,
  conda-forge only). `environment-lock.yml` is an exact Windows (win-64) build,
  for `conda env create -f environment-lock.yml` if an exact rebuild is ever
  needed. It does not work on Mac or Linux. Regenerated on 2026-09-23 from the
  second laptop: the two machines solved to the same 292 packages apart from
  `platformdirs` and `python-tzdata`, which is real evidence the environment is
  reproducible rather than an accident of one machine.
- Don't overwrite `environment.yml` with a generated export. It is hand-written
  and carries the reasoning for the Python 3.11 pin; `--from-history` produces
  the same package list but strips every comment and adds a personal `prefix:`
  path. Only `environment-lock.yml` is meant to be regenerated.
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

A cloud service account needs **two** IAM roles, and they fail one at a time,
so granting only the first looks like the key is broken:

| Role | Without it |
|---|---|
| `roles/serviceusage.serviceUsageConsumer` | "Caller does not have required permission to use project" |
| `roles/earthengine.writer` | "Permission 'earthengine.computations.create' denied on resource" |

Neither is a bad key. `src/check_ee.py` recognises both messages and names the
missing role. The project is registered `REGISTERED_NOT_COMMERCIALLY`, which
confirms service accounts do work on the Community tier. IAM changes take a
couple of minutes to propagate.

## Known issues

- **Fresh cloud containers ship a broken `cryptography`.** `import ee` fails
  with `ModuleNotFoundError: No module named '_cffi_backend'`, which names
  neither Earth Engine nor the real cause. Fix before anything else:
  `pip install --ignore-installed cffi cryptography`, then
  `pip install earthengine-api`. Plain `--upgrade` does not work, because the
  system package has no RECORD file for pip to uninstall from. This recurs in
  every new container.
- **`MKL_THREADING_LAYER=SEQUENTIAL` on Windows.** Without it, conda-forge's
  MKL kills Python with exit code -1066598273 (0xC06D007F, a failed delayed
  DLL load) and no Python error at all. It hit `terrain.moon_patch` on
  2026-11-13 and the `video` environment before. `environment.yml` sets it
  on `conda activate analog`; when calling `python.exe` directly without
  activating, set `$env:MKL_THREADING_LAYER = "SEQUENTIAL"` first. For an
  existing environment: `conda env config vars set -n analog
  MKL_THREADING_LAYER=SEQUENTIAL`.
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

## Machine-specific: Marwan's laptop

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

## Machine-specific: second Windows laptop (`C:\Users\user`)

Set up on 2026-09-23. It does **not** share Marwan's quirks: there is no stray
`C:\.git` here, so that warning does not apply on this machine.

- Project folder: `C:\Users\user\Desktop\NASA Hackathon\analog-finder`
- Miniforge 26.7.2 at `C:\Users\user\miniforge3`, installed `JustMe`, not on
  PATH, not registered as system Python. System Python 3.14.4 is separate and
  left untouched.
- Because conda is not on PATH, call it as
  `& "$env:USERPROFILE\miniforge3\Scripts\conda.exe"`, or dot-source
  `miniforge3\shell\condabin\conda-hook.ps1` before `conda activate` in a
  non-interactive shell. An interactive shell gets this from the profile that
  `conda init powershell` wrote.
- Smart App Control was already off (`VerifiedAndReputablePolicyState` = 0).
- Retry settings applied here on 2026-09-23, after `conda create` aborted part
  way through the downloads. `conda.anaconda.org` intermittently failed DNS
  (`getaddrinfo failed`) and took about 20 seconds to answer when it did, while
  the `prefix.dev` mirror answered in under a second. The solve and 254 of the
  packages had already succeeded, and re-running the identical command finished
  from the cache in minutes. Retry before changing anything else.
- Disk is the binding constraint here: about 41 GB free on `C:` against the
  25 to 40 GB the original plan expected for working-scale data. `conda clean -a`
  only returns about 0.5 GB, because most of `pkgs` is hardlinked into the
  environment, so it is not a useful lever.

## Where we are

*Update this section whenever the status changes.*

As of 2026-11-14 (hackathon 14 to 15 November), Phase 1 has passed, Prompts
1 and 2 are done and merged, and the global Earth grid (Prompt 3) covers
Africa and the Americas south of 50 N (merged in pull request #5). Every
twin has a shaded relief image (`shade/earth/<id>_<n>.webp`, n = place 1 to
25 in `matches/<id>.json`; `python src/render_shades.py`). The website is being built on `feature/website`, in a git
worktree at `C:\Users\Marwan\Desktop\analog-finder-website` (Marwan's
laptop); open Claude Code on that folder so the Impeccable design hooks run.

- **The Americas** (2026-11-13): 18,865 Mars-possible tiles, 1.43
  EECU-hours (stage A 0.03 run alone first with `--ndvi-only`, then stage B
  1.40 under a cap of 2 with `--reuse-ndvi`). A new ice filter (MODIS
  MCD12Q1 class 15, over 50% of a tile) keeps glaciers out. Read finished
  tables with `python src/earth_grid.py fetch <area>`: one big read hung for
  an hour. Jezero's closest twin is still the Egyptian tile, #1 of 148,925.

- **Diviner temperatures** (2026-11-14) are context on the Moon cards, not a
  matching feature: `src/run_diviner.py` (LRO Diviner south Polar Resource
  Product from PDS, MD5 checked) writes each region's temperatures and
  cold-trap and ice-stability shares, which `build_web_data.py` adds to
  `targets.json` as `diviner`. Never call the shares permanent shadow.

- **Targets are NASA's own sites** (Prompt 2, 2026-11-13). Mars: the 38
  candidate human Exploration Zones (`src/targets/mars_human_ez.json`).
  Moon: the nine Artemis III candidate regions of October 2024
  (`src/targets/moon_artemis.json`, outlines from USGS DOI 10.5066/P1MEQ6UK,
  checked against NASA's own table). Artemis III is now an Earth-orbit test
  flight and the first landing is Artemis IV; the file says so.
- **The Moon is matched on terrain only**, from the LOLA south pole DEM on
  NASA PGDA (`terrain.moon_patch`, averaged to 463 m like Mars and Earth),
  with its own scaler. Moon scores are low (best 5 to 33) because the pole
  is far rougher than almost any dry land, and are not comparable with Mars
  scores; every match also stores its rank (`rank` of `of`, e.g. 1 of
  148,925) and its rank within its continent (`rank_continent` of
  `of_continent`), which the website should show. Code: `src/run_moon_targets.py`,
  `src/build_web_data.py`.
- **Website data** is committed in `web/public/data/` (about 2.6 MB): targets,
  top 25 twins per target at least 25 km apart (true distance,
  `match_grid.top_spread`), the best Egyptian tile per target, shaded relief
  pairs. Rebuild with `python src/build_web_data.py`, then
  `python src/render_shades.py`.

- **Matching method is V1** (decided 2026-10-10): terrain + the Mars-possible
  filter (NDVI below 0.15, under 5% permanent water) + absolute albedo. Heat is
  not a matching feature; it only labels Mars tiles dusty, sandy or rocky, and
  Earth tiles get no label. Atacama and Death Valley take 92.5% of Mars
  matches. Within-world percentiles were tried and failed; don't reintroduce
  them. Code: `src/surface.py`, `src/run_thermal.py` (V2 with heat behind
  `--with-heat`). Details and history: `HANDOFF.md` sections 3 and 14.

- **Phase 1 validation passed on 2026-10-10, using elevation only.** Without
  being told about them, the model sent 73% of the Mars matches to Atacama and
  Death Valley. Code is in `src/terrain.py` and `src/run_phase1.py`, which
  also draws `figures/validation_elevation_only.png`. Earth elevation comes
  from the Copernicus DEM on AWS (no API key), with OpenTopography only as a
  backup. Details are in `HANDOFF.md` section 14 (History).

- **Earth elevation uses average resampling** (fixed 2026-10-12). MOLA's
  463 m pixels are averages, so Earth must be averaged too; rasterio's default
  nearest neighbour made Earth 6 to 9% rougher. Keep
  `resampling=Resampling.average` in `terrain.earth_patch`.

- **Global grid** (`src/earth_grid.py`, `src/match_grid.py`): Earth Engine does
  only coarse NDVI for every land tile, then water and albedo for tiles that
  pass NDVI, each export under a cost cap. Terrain is computed on the laptop
  from AWS with the validated code, one resumable file per 1 degree square in
  `data/processed/earth_grid/terrain/`. Egypt cost 0.2 EECU-hours. Details,
  costs and results: `HANDOFF.md` sections 2 and 14.

- **Done:** the `analog` environment is built on **two** Windows laptops and
  every import passes on both: Python 3.11.16, GDAL 3.12.3, rasterio 1.4.4,
  geopandas 1.1.4, scikit-learn 1.9.1. The repo has its structure, both
  environment files and `HANDOFF.md`. Earth Engine auth code (`src/config.py`,
  `src/check_ee.py`) was merged in PR #1.
- **Earth Engine works from the cloud.** `python src/check_ee.py` returns 0 in
  a cloud session using `GEE_SERVICE_ACCOUNT_KEY`: service account
  `analog-finder-bot@rare-decker-493720-c2.iam.gserviceaccount.com`, both IAM
  roles granted, SRTM reachable. The key is stored as an environment variable
  on the Claude cloud environment, base64 encoded, never in the repository.
- **Earth Engine works on Marwan's laptop** (`earthengine authenticate` done
  and `src/check_ee.py` passing, 2026-10-10). The second laptop still needs
  it. Inviting the remaining teammates is not done.
- **Judging and submission rules are in `docs/JUDGING_CRITERIA.md`**, and
  the challenge's official data list is in `docs/CHALLENGE_RESOURCES.md`
  (both added 2026-11-13). Read them before planning the final demo. In
  short: there is no live pitching; judges see only a **30 second video or
  exactly 7 slides**, uploaded first to the local Cairo form and then to the
  global Space Apps site. Still open: the Cairo PDF gives the event as
  **13 to 14 November** while this file says 14 to 15 (confirm); the GitHub
  repository is private, so judges cannot open its link until it is made
  public; the submission needs an AI-use disclosure. The final demo is
  planned for later.
- **Gemini chatbot** (2026-11-13): `src/chatbot.py` (Gemini, terminal mode),
  `src/chat_app.py` (Streamlit page), `src/chat_data.py` (lookups in
  `web/public/data/`, handed to Gemini as tools so it never invents a
  number), `src/chatbot_knowledge.md` (method facts it is given). Key in
  `GEMINI_API_KEY`, also set on the Claude cloud environment; never in a
  file. `gemini-2.5-*` is closed to new users and `gemini-3.8-flash` was
  often overloaded (503), hence the model fallback list; thinking "low"
  took replies from ~50 s to ~4 s. Tests: `tests/test_chat_data.py`
  (offline). `environment-lock.yml` does not have `google-genai` and
  `streamlit` yet; regenerate it on a Windows laptop. For the website, one
  team key (free tier) serves every visitor from the host's secrets;
  visitors need no key. **No per-visitor question limit, by team decision**
  (2026-11-13: "we'll be careful"); don't add one without asking. When the
  free quota runs out, visitors see "try again in a minute"
  (`chatbot.Busy`).
- **Next:** the website (`docs/WEBSITE_SPEC.md`), bringing `main`'s website
  data into `feature/website`, then the submission. Later: Prompt 4 in
  `docs/ENGINE_PROMPTS.md` (discoveries list and interface data), more
  continents for the grid (each estimated from a test country and run under
  a cost cap), and the known-analog validation.
