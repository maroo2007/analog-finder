# Project handoff

**Last updated:** 10 October 2026

Read this first if you are joining the project, or if you are an AI assistant
picking up work in a new session. It records what we are building, what has
already been done, and what has not.

---

## 1. The project

We are building a tool that finds places on Earth whose ground most closely
matches proposed landing and base sites on the Moon and Mars. Mission teams
train at a small number of Earth analog sites, mostly the Atacama Desert,
Haughton Crater and Death Valley. We think data can find more.

**Working name of the tool:** Planetary Twin Finder
**Team name:** not decided yet. See open decisions at the end.

### Event

NASA Space Apps Challenge 2026.

| What | When |
|---|---|
| Challenge titles released | 17 September 2026 |
| Full challenge statements and data lists | 28 October 2026 |
| Hackathon | 14 to 15 November 2026 |
| Judging begins | 16 November 2026 |

**Challenge chosen:** *Identify Earth Locations that Analog the Permanent Moon
Base Locations and Mars.* Tagged Advanced, Intermediate and Beginner/Youth.

Re-read the full statement on 28 October. It will name specific NASA data sets,
and judges score relevance to the stated challenge.

### Team

Computer science students at Egyptian Chinese University, Cairo. Strong on
software, weak on geology, which is the gap we are recruiting for.

---

## 2. How the tool works

Every place on every world gets the same short "report card" of numbers.
Finding twins is then a search for the closest report card.

**Features compared:**

- Mean slope, how steep the ground is
- Slope spread, whether steepness is even or mixed
- Relief, the height difference across a tile
- Thermal inertia, how fast the ground heats by day and cools at night, which
  separates dust from sand from solid rock
- Albedo, how much light the surface reflects
- Mineral signatures, added later

Earth has no standard thermal inertia product, so we use day temperature minus
night temperature from MODIS as a stand-in. Say clearly in the presentation that
this is a proxy, not the same measurement.

### Planned features

1. **Click and compare.** Click a spot on Mars or the Moon, Earth lights up with
   ranked matches.
2. **Mars-likeness map of all Earth.** One global score per Earth tile. This is
   the poster image.
3. **Analog Passport.** Per site: what it is good for testing, what it does not
   match, how hard it is to reach, and a score.
4. **Reverse mode.** Pick an Artemis site, find the cheapest Earth twin near a
   chosen city.
5. **Visual engine.** An image model such as DINOv2 compares what terrain looks
   like, alongside the physical comparison. Where both agree, confidence is
   higher.
6. **New analogs list.** Ten to twenty sites nobody currently uses, with reasons.
7. **Egypt field work.** Use our own tool to pick a site in the Western Desert,
   then photograph it next to the Mars image it matched.

### The validation test, which decides everything

The model is not told which sites NASA already uses. If it independently ranks
the Atacama, Haughton Crater and Death Valley near the top, the method is
credible and the new suggestions are believable. If it does not, fix the
features before building anything else. Publish the comparison either way.

A deliberate control is included: the **Nile Delta**, wet green farmland, which
should score badly. With elevation alone it may score well, because Mars has
flat plains too. That is expected, and it is the argument for adding thermal
and brightness data. Keep that first result as a slide.

---

## 3. Accounts and identifiers

No passwords or keys in this file, or in the repository. Ever.

| Service | Detail |
|---|---|
| NASA Earthdata | username `maroo_2007`, active, tested on AppEEARS |
| OpenTopography | registered, API key issued, stored privately off the repo |
| GitHub | user `maroo2007`, repository `analog-finder`, private |
| Google Earth Engine | approved for free noncommercial use until 22 March 2028 |
| Earth Engine project ID | `rare-decker-493720-c2` |

Every Python script that talks to Earth Engine begins:

```python
import ee
ee.Initialize(project='rare-decker-493720-c2')
```

Earth Engine tier is **Community**, which has a monthly compute quota and needs
no billing account. Never attach a credit card. Keep Earth Engine jobs coarse
and regional so the quota lasts.

---

## 4. Two data routes

**Plan A, Google Earth Engine.** Fast, no storage needed, handles global
analysis well. Approved and working.

**Plan B, direct downloads.** Copernicus DEM on AWS Open Data for elevation,
which needs no account or API key (OpenTopography is now only a backup), and
NASA AppEEARS for temperature and brightness. Slower and more manual, but nothing can revoke it,
and it works offline at the venue.

**Decision:** build on Plan B, use Plan A only for the global heatmap, and have
all data on local disk before the hackathon so no demo depends on the internet.

### Sources

| Need | Source |
|---|---|
| Mars elevation | MOLA global DEM, 463 m, USGS Astropedia, public domain |
| Mars thermal inertia | THEMIS global mosaic, USGS with ASU. Take the quantitative 32-bit version |
| Mars quick exports | JMARS map server, small files, fastest way to start |
| Moon elevation | LOLA, Astropedia or PDS Geosciences |
| Moon temperature | Diviner, PDS Geosciences |
| Earth elevation | Copernicus DEM GLO-30, AWS Open Data, no API key (used in Phase 1). Backup: OpenTopography or Earth Engine |
| Earth temperature | MODIS MOD11A1 and MYD11A1, day minus night |
| Earth albedo | MODIS MCD43A3 |
| Earth minerals | ASTER, and EMIT for Egypt |

Mars and Moon data need no account. Earth data does.

---

## 5. Storage

Keep to regions, not whole planets. Do Earth work in the cloud. Delete raw
files once the numbers are extracted.

- Test scale, coarse grids: under 1 GB
- Working scale, medium resolution with image tiles: 25 to 40 GB
- Recommended free disk: 100 GB, because every processing step writes a
  temporary copy

Full resolution globally would run to terabytes. We do not need it. Twin finding
compares the character of a landscape, not individual rocks.

---

## 6. Machine setup, as of this handoff

Windows machine. Project folder: `C:\Users\Marwan\Desktop\Nasa Space Apps 2026`

The folder name has spaces, so quote every path in commands.

**Done:**

- Git 2.53.0 and Node 24.14.1 already present
- System Python is 3.14, left untouched. Too new for rasterio and GDAL, which
  is why conda builds its own
- Miniforge 26.7.2 installed at `C:\Users\Marwan\miniforge3`, user-only install,
  not added to PATH, system Python not registered
- Installer SHA256 verified against the GitHub release before running
- Channels: conda-forge. Anaconda defaults are not used. Miniforge also ships
  a `prefix.dev` mirror of conda-forge, kept on purpose because a second
  source helps on a flaky connection
- `conda init powershell` run, profile created at
  `C:\Users\Marwan\Documents\WindowsPowerShell\profile.ps1`
- Base auto-activation turned off
- `analog` environment built from conda-forge and every import tested:

  | Package | Version |
  |---|---|
  | Python | 3.11.16 |
  | GDAL | 3.12.3 |
  | rasterio | 1.4.4 |
  | geopandas | 1.1.4 |
  | scikit-learn | 1.9.1 |
  | numpy / pandas / matplotlib | 2.4.6 / 3.0.6 / 3.11.2 |
  | jupyterlab / earthengine-api | 4.6.4 / 1.7.45 |

- Repository cloned into the project folder itself, which is now the repo root
- `data/raw`, `data/processed`, `notebooks`, `src` created, each with a
  `.gitkeep`. `.gitignore` lets only the `.gitkeep` files through under `data/`
- `environment.yml` (portable, unpinned) and `environment-lock.yml` (exact
  Windows build) written and committed
- Sherif's Earth Engine code merged via PR #1: `src/config.py` holds the
  project ID and handles both laptop login and a cloud service account key;
  `src/check_ee.py` checks the connection
- `CLAUDE.md` added, so Claude Code sessions on any laptop share the same
  rules and status

Rebuild the environment with:

```bash
conda env create -f environment.yml
conda activate analog
```

Solving took 14 minutes the first time and 5 minutes on the retry, which is
normal for GDAL. If the environment ever has to be rebuilt and 3.11 will not
solve, use Python **3.12**. Do not jump to 3.13 or 3.14; rasterio and GDAL lag
behind.

### Problems we hit, in case they happen again

- **Dropped connection during download.** The first `conda create` failed
  with `Connection broken: IncompleteRead`. The file that broke was `mkl`
  (109 MB, Intel's maths library), the largest in the environment. conda's
  retry settings were raised (`remote_max_retries 6`,
  `remote_read_timeout_secs 120`, `remote_connect_timeout_secs 60`), and the
  retry reused everything already downloaded and finished cleanly. If `mkl`
  keeps failing, `nomkl` avoids it.
- **Smart App Control blocked pandas.** Windows 11's Smart App Control
  refused to load unsigned compiled Python files, so `import geopandas`
  failed with "An Application Control policy has blocked this file". It was
  turned off on 23 September, and every import now passes. Every teammate on
  Windows 11 needs to turn it off too.

**Not done yet:**

- `earthengine authenticate` on this laptop, needed once before Python can
  reach Earth Engine. Then run `python src/check_ee.py`
- Invite the remaining teammates on GitHub, and have each make their own
  Earthdata account

### A known oddity

Someone once ran `git init` at `C:\`, so Git treats the whole drive as one
repository, and thousands of old Flutter files show as deleted. It is harmless
because our repository has its own history. **Do not commit those changes, and
do not delete `C:\.git` casually.** Leave it until someone has time to look
properly.

---

## 7. Build order

Phase 1 is the gate. Everything else waits on it.

1. **Small test.** Coarse Mars and Earth grids, elevation only, three or four
   regions including the Nile Delta control. Build the report cards, build the
   similarity search, and run the validation test.

   **Passed on 10 October 2026, using elevation only.** Without being told
   which sites NASA uses, the model sent 73% of the Mars matches to Atacama
   and Death Valley. By Mars site, the two known analogs took 92% of Jezero's
   matches, 96% of Gale's and 30% of Meridiani's. The Nile Delta control
   scored only on Meridiani, a flat plain, as expected, which is the case for
   adding thermal data next. Code: `src/terrain.py` and `src/run_phase1.py`.
   Chart: `figures/validation_elevation_only.png`.
2. **Scale up.** Add thermal inertia, albedo, minerals. Raise resolution inside
   the chosen regions. Add the Moon. Build the global heatmap and the new
   analogs list.
3. **Visual engine.** Image tiles, DINOv2 on Colab, compare with the physical
   engine.
4. **Application.** Clickable globe, Earth heatmap, passport cards, reverse
   mode, works on a phone.
5. **Egypt.** Pick the site with our own tool, visit it, photograph it.
6. **28 October.** Read the full statement, add the data sets it names.
7. **Rehearse.** Fix the scope for the 48 hours, script the demo, record a
   backup video and screenshots in case the live demo fails.
8. **14 to 15 November.** Build, then submit at least three hours early.

### Sanity checks that save hours

- Test every data source on a known answer first. Cut Olympus Mons out of the
  Mars map: if a giant round mountain appears, the coordinates are right.
- Put Earth and Mars on the same pixel size before comparing anything, or Earth
  will look rougher for no real reason.
- Normalize features before measuring distance, or relief in metres will drown
  out slope in degrees.
- Commit after every working step.

---

## 8. Rules we work by

- No secrets in the repository. `data/`, `*.tif`, `.env`, `keys.txt` and `*.key`
  are all in `.gitignore`.
- Verify the fingerprint of any installer before running it.
- Read code before running it. A judge may ask how the similarity engine works,
  and "the AI wrote it" is not an answer.
- Name every NASA data source on the project page. Judges check it.
- Be honest about what the model does not match. Admitting a limit reads as
  competence.

---

## 9. Open decisions

- **Team name.** Shortlist: Ta-Desher (ancient Egyptian for "the red land"),
  Stunt Double, Mirage, KA, The Understudy. Check it is not already taken on
  the Space Apps site.
- **Which Egyptian site** to study and photograph. Bahariya and the Black
  Desert are the leading candidates.
- **Whether to visit it in person.** The only real cost in the project.
- **Recruiting.** We need someone who knows geology, remote sensing or
  geography, even if they have never written code.

---

## 10. Everything else is free

NASA and USGS data, Python and every library, DINOv2, Earth Engine on the
Community tier, Colab's free GPU, GitHub, Netlify or GitHub Pages hosting, and
the hackathon entry itself. The real budget is time and computer power.
