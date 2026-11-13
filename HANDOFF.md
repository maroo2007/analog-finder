# Project handoff

**Last updated:** 13 November 2026, the day before the hackathon.

Read this first if you are joining the project, or if you are an AI assistant
picking up work in a new session. It says what we are building, what is
finished, what is running right now, and what is left. Day-to-day rules for
Claude Code sessions, machine quirks and known Windows issues are in
`CLAUDE.md`.

---

## 1. The project in one paragraph

**Planetary Twin Finder** finds the places on Earth whose ground best matches
the sites NASA has proposed for landing humans on Mars and on the Moon.
Astronauts and equipment are tested at a few Earth analog sites (the Atacama
Desert, Death Valley, Iceland, Devon Island), most of them chosen through field
experience and habit. Nobody has compared the whole planet against the actual
target sites. We describe every patch of ground on Earth, Mars and the Moon
with the same few numbers, remove Earth ground that has plants or water, and
rank the Earth places closest to each NASA site, saying honestly what matches
and what doesn't.

| | |
|---|---|
| Event | NASA Space Apps Challenge 2026 |
| Challenge | *Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars* |
| Team | **Duplica**, computer science students at Egyptian Chinese University, Cairo |
| Hackathon | **14 to 15 November 2026** (judging from 16 November) |
| Repository | GitHub `maroo2007/analog-finder`, private |

---

## 2. Where we are (13 November 2026)

### Finished and on `main`

- **Matching method (V1), validated.** Without being told which Earth sites
  NASA uses, the program sent **92.5%** of its Mars matches to the Atacama
  Desert and Death Valley, NASA's best-known analogs. A wet
  farmland control (the Nile Delta box) got 7.5%, and those were desert tiles
  east of Cairo, not farmland.
- **Africa grid.** 368,405 land tiles profiled, 130,060 of them
  "Mars-possible" (no plants, no water).
- **Mars targets.** NASA's **38 candidate human Exploration Zones**, each
  matched against all of Africa.
- **Moon targets.** NASA's **nine Artemis III candidate regions** near the
  lunar south pole, matched on terrain.
- **Website data.** Everything the site needs for Africa, Mars and the Moon
  is built and committed in `web/public/data/` (about 6 MB). See section 6.
- **Registration (6 to 7 November).** Cairo registration form, an 88 second
  YouTube video in Egyptian Arabic with English captions, and a two-page
  English proposal PDF.

**Headline result:** Jezero's closest twin is Egypt's Eastern Desert tile,
**#1 in Africa and #1 of 148,925 overall**, ahead of the Atacama and Death
Valley. **Jezero crater** is where Perseverance landed; the tile is inland
from the Red Sea at 25.125 N, 34.54 E (score 73.3 with the Americas in the
grid, 67.9 with Africa alone; the score moves because features are
standardized over more tiles, the ranking method does not). It is dark
ground, which is what Mars's dark sites need, and the area is rarely studied
as a Mars analog.

> **Number to use everywhere: 92.5% (say "92%").** In the registration video
> one speaker said "96%" by mistake. That number is wrong. Every final
> material (slides, demo video, website, answers to judges) uses 92.5%.

### The Americas (merged into `main` on 2026-11-14, pull request #5)

North and South America **south of 50 N** are now in the Earth grid, so the
Atacama, Death Valley and the Andes are on the map.

- **New ice filter.** Snow and ice have no plants, so they slipped through
  the NDVI test. Tiles more than 50% permanent snow and ice (MODIS land cover
  MCD12Q1, class 15) are now dropped. Checked: 0.92 ice on the Patagonian Ice
  Field, 0.00 in the Atacama. It removed 247 false "Mars twins" in Chile.
- **Chile test done:** 0.20 EECU-hours, 7.2 minutes, 11,097 land tiles, 3,801
  Mars-possible, the Atacama 97% Mars-possible.
- **Stage A (NDVI only), cap 0.5:** 0.03 EECU-hours. 396,555 land tiles,
  20,396 pass NDVI (5%; the 0.15 threshold is strict, so sagebrush, Sonoran
  shrubs and the Patagonian steppe mostly fail). Run alone first
  (`--ndvi-only`) so stage B could be estimated from its real workload.
- **Stage B (water, albedo, ice), cap 2:** **1.40 EECU-hours**, above the 0.3
  to 1.0 estimate (6.9 per 100k passing tiles, against 1.4 for Africa and 4.7
  for Chile: the American desert tiles are scattered, so the 30 m water layer
  is evaluated over many blocks). Total for the Americas 1.43.
- **Result:** **18,865 Mars-possible tiles**, all with terrain (499 one
  degree squares on the laptop, none failed). After NDVI, 1,228 tiles were
  removed for permanent water and 303 for ice. By country: United States
  5,894, Argentina 5,141, Chile 3,801, Mexico 1,496, Bolivia 1,240, Peru
  1,163, Canada 123.
- **Known analogs still Mars-possible** (tiles within 30 km): Atacama 38 of
  38, Death Valley 31 of 40, Hanksville, Utah (MDRS) 39 of 42.
- **Reading the results back:** one request for the 396,555-row table hung for
  over an hour with no error. `python src/earth_grid.py fetch americas` reads
  finished tables in 5 degree latitude bands with a deadline and retries (no
  new compute); it took 14 minutes including terrain.
- **Website data rebuilt** with both continents: 148,925 Mars-possible tiles
  (Africa 130,060, the Americas 18,865). Every match and Egypt row now also
  has `continent`, `rank_continent` and `of_continent`. Mars best scores 63
  to 98; 32 zones' best twins are in Africa, 6 in the Americas (Gale's in the
  United States). Moon best scores 5 to 33, all nine in the Americas (mostly
  the Andes, which are much closer to the south pole's roughness than dry
  Africa). Malapert's best Egyptian tile is now 34 of 130,060 in Africa.

### Left to do, in order

| # | Task | Notes |
|---|---|---|
| 1 | **The website** | In progress on `feature/website`. The most important piece: it is what judges see. Spec in section 7. |
| 2 | Refresh the website data | The Americas are merged; bring `main`'s `web/public/data/` (both continents, a shaded relief image for every twin) into `feature/website`. |
| 3 | Publish the site on a public link | See section 7, hosting. |
| 4 | **Final submission, 15 November** | Section 8. 30 second English video or up to 7 slides, public link. |
| 5 | Nice to have, only if time is left | Discoveries list (Prompt 4 in `docs/ENGINE_PROMPTS.md`), Hawaii (Mauna Kea), more continents, Moon albedo/thermal. |

Out of scope for this hackathon: the image AI (DINOv2), reverse mode by city,
and the Egypt field trip.

---

## 3. How the matching works

**Tiles.** Every world is cut into tiles of 20 x 20 pixels at **463 m per
pixel** (about 9.26 km across). 463 m is the resolution of NASA's Mars
elevation map (MOLA), so Earth and the Moon are **averaged** down to the same
pixel size first. Averaging matters: MOLA pixels are averages, and reading
Earth with nearest-neighbour sampling made it 6 to 9% rougher for no real
reason (fixed 12 October).

**Four numbers per tile:**

| Feature | Meaning | Mars | Moon | Earth |
|---|---|---|---|---|
| Slope (`mean_slope`) | how steep, on average | MOLA | LOLA | Copernicus DEM |
| Roughness (`slope_spread`) | whether steepness is even or mixed | MOLA | LOLA | Copernicus DEM |
| Relief (`relief`) | highest minus lowest point in the tile | MOLA | LOLA | Copernicus DEM |
| Brightness (`albedo`) | how much light the ground reflects | TES | not used yet | MODIS MCD43C3 |

**Mars-possible filter (Earth only).** A tile is kept only if its median NDVI
is below 0.15 (no plants), under 5% of it is permanent water (JRC), and, in
the Americas, under 50% of it is permanent snow and ice (MCD12Q1).

**Distance and score.** Features are standardized together (one scaler per
world comparison). A tile's distance to a target is its mean distance to the
target's 10 nearest tiles. **Score = 100 x exp(-distance / 0.4)**, so 100 is a
perfect match. Twins in a list are at least 25 km apart (true distance,
`match_grid.top_spread`). Every match also stores its **rank** among all
Mars-possible Earth tiles ("1 of 148,925"), its rank within its own continent
(`rank_continent` of `of_continent`, "1 of 130,060 in Africa"), and a
per-feature **closeness**
(100 when a feature matches exactly, 0 at two standard deviations).

**The Moon is different.** It is matched on terrain only (no brightness), with
its own scaler. Its scores are low (best 5 to 33, against 63 to 98 for Mars)
because the lunar south pole is far rougher than almost any dry land. With
the Americas in the grid all nine best twins are there, mostly in the Andes;
in Africa only volcanic mountains come close (Tibesti in Chad, Afar, the
Atlas).
**Moon and Mars scores can't be compared. Show the rank for the Moon.**

**What we tried and rejected** (keep for judges' questions):
- **Heat as a matching feature.** On Earth the MODIS day-night temperature
  mostly measures soil moisture; on Mars it measures rock versus dust. Not the
  same thing, so it is not used for matching (V2 stays in the code behind
  `python src/run_thermal.py --with-heat`). Heat only labels Mars tiles as
  dusty, sandy or rocky; Earth tiles get no label.
- **Percentiles within each world.** Made the farmland control rise to 29%.
  Don't reintroduce it.

Validation history, in short:

| Variant | Atacama + Death Valley | Nile Delta box |
|---|---|---|
| Elevation only | 73.0% | 11.6% |
| + filter | 73.2% | 7.0% |
| Percentiles (rejected) | 71.7% | 28.3% |
| **V1: terrain + filter + albedo** | **92.5%** | **7.5%** |
| V2: V1 + heat | 84.3% | 15.6% |

---

## 4. The targets

**Mars: 38 human Exploration Zones** (`src/targets/mars_human_ez.json`), read
from the georeferencing of the USGS CTX_EZs mosaics
(`asc-pds-services.s3.us-west-2.amazonaws.com/wms_basemaps/Mars/CTX_EZs/`),
duplicates removed. Each is profiled from a 400 x 400 pixel MOLA patch
(about 185 km) around its centre (`src/run_mars_targets.py`).

**Moon: nine Artemis III candidate regions** (`src/targets/moon_artemis.json`):
Peak Near Cabeus B, Haworth, Malapert Massif, Mons Mouton Plateau, Mons
Mouton, Nobile Rim 1, Nobile Rim 2, de Gerlache Rim 2, Slater Plain. NASA's
release (28 October 2024) gives no coordinates, so outlines come from the USGS
data release *Down Selected Artemis III Candidate Landing Site Navigational
Grids* (DOI 10.5066/P1MEQ6UK, file `A3_9regions-lonlat-simplified.zip`), and
were checked against NASA's own table (NTRS 20250007692): every centre within
5 km, every area within 0.1%. A third check, against the 2022 region elevation
models on Zenodo (record 17954508), could not run: Zenodo answered HTTP 429
(too many requests) on 13 November. Caveat written into the file: Artemis III
is now an Earth-orbit test flight, the first landing is Artemis IV (2028), and
its site isn't chosen yet.

Moon elevation: LOLA south pole DEM, 80 m, polar stereographic, NASA PGDA
(Barker et al. 2023), averaged to 463 m (`terrain.moon_patch`). Known answer:
Shackleton crater comes out 4.06 km deep (published 4.2 km). Each region's box
is its extent plus 15 km a side, at least 120 pixels; no box reaches the pole.

**Moon upgrades, later:** the Moon has no brightness or heat feature yet. Two
open NASA data sets would add them: **Diviner thermal** (LRO's radiometer:
rock abundance and night-time temperature, the Moon's version of the Mars
heat layer) and **LOLA albedo** (LOLA's 1064 nm normal albedo, available for
the polar regions). Either needs the same check as Mars heat first: that it
measures the same thing on both worlds.

---

## 5. Data sources and credits

| World | Data | Source |
|---|---|---|
| Mars | MOLA elevation, 463 m | NASA MGS, USGS Astropedia (public domain) |
| Mars | TES albedo | NASA MGS, USGS Astropedia |
| Mars | Exploration Zones | USGS CTX_EZs mosaics |
| Mars | Colour mosaic (`web/public/img/mars.jpg`) | Viking, NASA/JPL/USGS |
| Moon | LOLA south pole DEM, 80 m | NASA PGDA (Barker et al. 2023, doi:10.60903/gsfcpgda-lola-spole) |
| Moon | Artemis III regions | NASA, outlines from USGS DOI 10.5066/P1MEQ6UK, drawn from LROC QuickMap (ASU, `quickmap.lroc.asu.edu`) |
| Earth | Copernicus DEM GLO-30 | ESA, AWS Open Data, no key (attribution below) |
| Earth | NDVI MOD13C1, albedo MCD43C3, land cover MCD12Q1 (the grid) | NASA MODIS via Google Earth Engine |
| Earth | NDVI MOD13A2, albedo MCD43A3 (the 92.5% validation, `src/surface.py`) | NASA MODIS via Google Earth Engine |
| Earth | Permanent water | JRC Global Surface Water via Earth Engine |

Everything is open data. Name every NASA source on the website and in the
submission; judges check.

**Copernicus DEM attribution, required by its licence.** We average it,
derive slopes from it and draw shaded relief from it, so the data are
"adapted or modified", which the licence (Article 6, (b) and (c)) covers with
this notice, word for word:

> produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus
> Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European
> Union and ESA; all rights reserved

and, wherever we publish it, this sentence:

> The organisations in charge of the Copernicus programme by law or by
> delegation do not incur any liability for any use of the Copernicus
> WorldDEM-30.

Source: the licence PDF on the Copernicus Data Space Ecosystem,
`documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/DEM/resources/license/License-COPDEM-30.pdf`.

---

## 6. The website data (already built)

All in `web/public/data/`, committed, rebuilt with
`python src/build_web_data.py`, then `python src/render_shades.py` and
`python src/render_shades.py --twins` (about 50 minutes; skips files that
exist, so delete `shade/` first after a data rebuild).

| File | Contents |
|---|---|
| `targets.json` | `features`: the four feature keys with label and unit. `targets`: 47 entries (38 Mars, 9 Moon) with `id`, `name`, `world` (`mars`/`moon`), `lat`, `lon`, `bbox`, `matched_on`, median `features`, `best_score`. Moon entries also have `code` (USGS region code, e.g. `MA`), `outline`, `area_km2` and a `note`. |
| `matches/<id>.json` | Top 25 Earth twins for that target: `lat`, `lon`, `country`, `continent`, `score`, `rank`, `of`, `rank_continent`, `of_continent`, `features`, `closeness` per feature. |
| `egypt.json` | Best Egyptian tile per target: `target`, `lat`, `lon`, `score`, `rank`, `of`, `rank_continent`, `of_continent` (Africa). |
| `likeness.png`, `likeness_americas.png` + `likeness.json` | The "how Mars-like" map per continent. `likeness.json` lists `maps` (`area`, `image`, `bounds`) and keeps `bounds` for Africa ([[-35, -18], [38, 52]], lat/lon); the Americas are [[-56.5, -125], [50, -34]]. |
| `shade/mars/<id>.png`, `shade/moon/<id>.png` | Shaded relief of each target, 65 km across. |
| `shade/earth/<id>_top.png`, `<id>_egypt.png` | Shaded relief of its best twin and its best Egyptian tile, drawn the same way. |
| `shade/earth/<id>_<n>.webp`, `<id>_egypt.webp`, `shade/<world>/<id>.webp` | The same, 200 px WebP, for every twin: `n` is the twin's place (1 to 25) in `matches/<id>.json`, so `_1` is `_top`. 1,269 files, 1.7 MB. |
| `web/public/img/mars.jpg` | Mars global colour map (Viking). |

**Missing for the site:** a Moon south pole base map image (can be rendered
from the same LOLA DEM with `moon_patch`).

---

## 7. The website to build

The full website spec is docs/WEBSITE_SPEC.md: a scroll-story page that
explains the project scene by scene and ends on a button that opens the
Twin Finder. It is built with the Impeccable design skill
(https://github.com/pbakaus/impeccable), which decides fonts and shapes;
the spec pins the content, the storyboard and the world colours.

English, one main page plus two small ones, dark space theme, works on a phone.
Static site (HTML/JS, or Vite + React), no server, reads the JSON files above.

**Home**
- Name, one line: *Find the places on Earth that best match NASA's proposed
  Mars and Moon sites.*
- The headline discovery up front: Jezero crater next to Egypt's Eastern
  Desert, "#1 in Africa, #1 of 148,925".
- Two buttons: **Explore Mars**, **Explore the Moon**.
- Three small steps: cut each world into tiles, give each tile the same
  profile, find the closest.

**Explorer (the main page)**
- Split screen. One side: Mars (38 zones as points on `mars.jpg`) or the
  Moon south pole (9 regions as outlines), with a Mars / Moon switch.
- Other side: an Earth map. Before a choice, it shows the likeness maps over
  Africa and the Americas. After clicking a target, its 25 twins appear as numbered pins, with
  a list underneath.
- Earth map: Leaflet or MapLibre with an open base map. Mars and Moon: an
  image with a simple coordinate system.

**Twin card** (opens on a pin)
- The two shaded relief images side by side (target and twin).
- Rank ("#1 of 148,925", and "#1 in Africa" from `rank_continent`) and
  score. **For the Moon, show the rank first.**
- One bar per feature with its closeness (four for Mars, three for the Moon).
- Two honest sentences: what matches, what doesn't.
- A fixed line: no place on Earth copies gravity, atmosphere or radiation.
- Country, coordinates, "Open in Google Maps".

**Egypt Spotlight**: the best Egyptian tile for every target, with its rank.

**About**: method, the 92.5% validation, data and credits, limits, team, how we
used AI.

**Colours:** Mars rust orange, Moon silver grey, Earth sand and blue.
**Don't design for data we don't have** (photos of places, user ratings).

**Hosting.** The repo is private. GitHub Pages on a private repo needs GitHub
Pro (free with the GitHub Student Developer Pack); otherwise Netlify or Vercel
free tiers deploy the `web/` folder. The link must be public for judging.

---

## 8. Final submission rules (15 November)

- A demo video of **30 seconds or less with English subtitles**, or **up to 7
  slides**, plus a **public** project link.
- Say how AI was used (Claude helped write code, scripts and documents).
- **No NASA logos or branding** (writing "NASA" in text is fine).
- AI-generated images or video need a visible watermark; we use none.
- Credit every asset (section 5). The registration video's credits list is in
  `video/credits.txt` on Marwan's laptop.
- Submit at least three hours before the deadline.

---

## 9. Accounts and Earth Engine

No passwords or keys in this file or the repository. Ever.

| Service | Detail |
|---|---|
| NASA Earthdata | username `maroo_2007` |
| GitHub | `maroo2007/analog-finder`, private |
| Google Earth Engine | project `rare-decker-493720-c2`, Community tier, noncommercial until 22 March 2028 |

- **Never attach a billing account or card.** Community tier: 150 EECU-hours a
  month, resets on the 1st.
- **Every Earth Engine export runs under a cost cap** (`earth_grid.run_capped`)
  and is estimated first from a realistic test country. On 10 October an
  uncapped export burned 14.7 EECU-hours.
- November so far: Chile test 0.20, Americas stage A 0.03 and stage B 1.40,
  so about 1.63 EECU-hours of batch compute. Earth Engine's task list kept no
  history before these, so check the Cloud Console usage page for the full
  month.
- In code use `from config import init_ee; ee = init_ee()`. Cloud sessions use
  the `GEE_SERVICE_ACCOUNT_KEY` environment variable (details in `CLAUDE.md`).

---

## 10. Code map

| File | What it does |
|---|---|
| `src/terrain.py` | Reads MOLA, Copernicus DEM and LOLA; `report_cards` makes the per-tile features |
| `src/surface.py` | Albedo, NDVI, water, ice and the Mars-possible filter |
| `src/earth_grid.py` | Earth Engine exports under cost caps, local terrain per 1 degree square |
| `src/match_grid.py` | Ranks Earth tiles against a target; `top_spread` (25 km rule) |
| `src/run_mars_targets.py`, `src/run_moon_targets.py` | Profile the NASA targets |
| `src/build_web_data.py` | Writes `web/public/data/` |
| `src/render_shades.py` | Shaded relief images |
| `src/run_phase1.py`, `src/run_thermal.py` | The validation runs and the rejected heat variant |
| `tests/` | 70+ offline tests; network tests are marked and skipped by default |
| `docs/ENGINE_PROMPTS.md` | The prompts used to build the engine, in order |

Data stays in `data/` (gitignored): `data/processed/earth_grid/` holds the grid,
one resumable terrain file per 1 degree square.

Setup: `conda env create -f environment.yml`, `conda activate analog`,
`earthengine authenticate`, `python src/check_ee.py`. Windows issues (MKL crash,
Smart App Control, conda downloads) are in `CLAUDE.md`.

---

## 11. Limits (say these out loud)

- Matching uses terrain shape and brightness at about 460 m. No rock
  chemistry, no temperature, no boulders.
- The Moon has no brightness feature yet, and its polar lighting and permanent
  shadow have no Earth equivalent.
- The Earth grid covers Africa and the Americas south of 50 N. The rest of the
  world isn't scored yet.
- Earth and Mars albedo come from different instruments and atmospheres;
  small differences mean little.
- Results are a ranked, explained shortlist for field teams, not a substitute
  for visiting a site.

---

## 12. Rules we work by

- No secrets in the repository.
- Verify the fingerprint of any installer before running it.
- Read code before running it. A judge may ask how it works, and "the AI wrote
  it" is not an answer.
- Name every NASA data source. Be honest about what doesn't match.
- Commit after every working step. Claude Code explains each command and waits
  for approval (`CLAUDE.md`).

## 13. Open decisions

- Whether the final demo is the 30 second video or slides.
- Where to host the site (section 7).
- Recruiting someone who knows geology or remote sensing is still welcome.

---

## 14. History

Kept from the 10 October to 13 November handoff, for judges' questions and
for anyone checking how the numbers came about.

**Phase 1 validation (10 October 2026), elevation only.** Without being told
which sites NASA uses, the model sent 73% of the Mars matches to Atacama and
Death Valley. By Mars site, the two known analogs took 93% of Jezero's
matches, 96% of Gale's and 30% of Meridiani's (after the 12 October
resampling fix; 92%, 96% and 30% before). The Nile Delta control scored only
on Meridiani, a flat plain, as expected, which is the case for the Mars
filter and albedo. Code: `src/terrain.py` and `src/run_phase1.py`, which also
draws `figures/validation_elevation_only.png`.

**Cost incident (10 October 2026).** A first, uncapped Africa export computed
30 m water over the whole bounding box, ocean included, and burned **14.7
EECU-hours** before it was cancelled by hand. It had been estimated at 5 from
a single all-land 1 degree square, which hid both the ocean and the overhead.
Since then every Earth Engine export runs under a cost cap
(`earth_grid.run_capped`, polled every 10 seconds), and costs are estimated
from a realistic test country first. Measured on one 1 degree square, terrain
was 87% of the old cost; reading it locally removed it.

**Egypt test area (cap 1): 0.20 EECU-hours.** 12,820 land tiles, 11,694
Mars-possible. Best matches against the three Phase 1 Mars sites (before
NASA's zones were added), at least 25 km apart:

| Mars site | Egyptian tile (lat, lon) | Slope | Relief | Albedo |
|---|---|---|---|---|
| Jezero | 25.2917, 34.5417 | 2.0 deg | 214 m | 0.139 |
| Jezero | 24.7083, 34.9583 | 1.9 deg | 223 m | 0.156 |
| Jezero | 23.9583, 35.2917 | 1.7 deg | 185 m | 0.147 |
| Gale | 22.8750, 35.1250 | 0.7 deg | 117 m | 0.229 |
| Gale | 24.2083, 33.3750 | 0.8 deg | 107 m | 0.220 |
| Gale | 24.0417, 35.3750 | 0.8 deg | 122 m | 0.235 |

Jezero's best twins are dark ground in the Eastern Desert inland from the Red
Sea, as the albedo finding predicted (the Mars sites have albedo 0.15 to
0.22; most Earth desert is brighter, the Black Desert box has median 0.40).
`python src/match_grid.py egypt Jezero Gale` prints the full lists with
Google Maps links.
