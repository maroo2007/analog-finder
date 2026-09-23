# Project handoff

**Last updated:** 22 September 2026

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

**Plan B, direct downloads.** OpenTopography for elevation, NASA AppEEARS for
temperature and brightness. Slower and more manual, but nothing can revoke it,
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
| Earth elevation | Copernicus GLO-30 or GLO-90, via Earth Engine or OpenTopography |
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
- Channels: conda-forge only, Anaconda defaults not in use
- `conda init powershell` run, profile created at
  `C:\Users\Marwan\Documents\WindowsPowerShell\profile.ps1`
- Base auto-activation turned off

**In progress at time of writing:** creating the `analog` environment. Solving
took about 14 minutes, which is normal for ten packages including GDAL on
Python 3.11. Download and install followed.

```bash
conda create -n analog -c conda-forge python=3.11 rasterio gdal numpy pandas \
  matplotlib scikit-learn geopandas jupyterlab requests earthengine-api
conda activate analog
```

If the environment ever has to be rebuilt and 3.11 will not solve, use Python
**3.12**. Do not jump to 3.13 or 3.14; rasterio and GDAL lag behind.

**Not done yet:**

- `earthengine authenticate`, needed once before Python can reach Earth Engine
- Clone the repository into the project folder
- Create `data/raw`, `data/processed`, `notebooks`, `src`
- Write `environment.yml` so teammates can rebuild the environment
- Invite teammates on GitHub, and have each make their own Earthdata account

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
