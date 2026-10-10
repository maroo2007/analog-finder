# Engine prompts for Claude Code

Written 10 October 2026. Paste each prompt into Claude Code, one at a time, on
the laptop that holds the repo. Each one ends with Claude Code stopping for
your approval, so nothing gets committed without you seeing it.

Order:

| # | What | Depends on | Who |
|---|---|---|---|
| 0 | Save Phase 1, set up the test suite | nothing | anyone, first |
| 1 | Heat, brightness, and the "could this be Mars" filter | 0 | Earth person |
| 2 | Real target sites: NASA's Mars landing zones and Artemis Moon regions | 0 | Mars/Moon person |
| 3 | Score the whole Earth | 1 | Earth person |
| 4 | Discoveries list and the data the interface reads | 2 and 3 | either |
| 5 | Image AI (optional) | 0 | anyone with spare time |

Prompts 1 and 2 can run at the same time on two laptops, each on its own
branch.

Data sources below were checked on 10 October and all open with no key:

- Mars elevation: `planetarymaps.usgs.gov/mosaic/Mars_MGS_MOLA_DEM_mosaic_global_463m.tif`
- Mars brightness: `planetarymaps.usgs.gov/mosaic/Mars_MGS_TES_Albedo_mosaic_global_7410m.tif`
- Mars night-time infrared, 60N to 60S, 100 m, with overviews:
  `asc-pds-services.s3.us-west-2.amazonaws.com/wms_basemaps/Mars/THEMIS_ASU/Mars_MO_THEMIS-IR-Night_mosaic_60N60S_100m_v14_clon0.tif`
- Mars human landing zones, one GeoTIFF per zone:
  `asc-pds-services.s3.us-west-2.amazonaws.com/wms_basemaps/Mars/CTX_EZs/`
- Moon elevation: `planetarymaps.usgs.gov/mosaic/Lunar_LRO_LOLA_Global_LDEM_118m_Mar2014.tif`
  (8.5 GB, not tiled, so read windows only)
- Earth elevation: Copernicus DEM 30 m on AWS Open Data

Not available: the quantitative THEMIS thermal inertia mosaic. Its links return
404. The night infrared mosaic stands in for it, as explained in prompt 1.

---

## Prompt 0: save Phase 1 and set up the test suite

```
Read CLAUDE.md and HANDOFF.md first. Fetch and pull before anything else.

1. src/terrain.py, src/run_phase1.py and figures/validation_elevation_only.png
   are already in the folder but not committed. Run python src/run_phase1.py
   in the analog environment. The shares should be close to Atacama 45%,
   Death Valley 28%, Black Desert 14%, Nile Delta 13%. Tell me if they
   differ by more than a few points.

2. Add pyarrow to environment.yml and install it in analog. We will store
   feature tables as Parquet.

3. Create tests/test_validation.py with pytest. These are known-answer tests
   that protect the science as the code grows. They read live data, so mark
   them with @pytest.mark.network and keep each under a minute:
   - Olympus Mons summit from MOLA is between 20,500 and 22,000 m
   - Jezero crater floor is below -2,000 m
   - In the Phase 1 comparison, Atacama plus Death Valley take at least 60%
     of all Mars matches
   - A placeholder test, skipped for now, that will assert the Nile Delta
     takes under 5% once thermal data exists

4. Update HANDOFF.md: Phase 1 validation passed on 10 October using
   elevation only. Atacama and Death Valley took 73% of Mars matches without
   being told they are known analogs. Earth elevation now comes from
   Copernicus DEM on AWS Open Data with no key, so OpenTopography is only a
   fallback.

Show me git status and the diff, then wait. Commit and push only after I say
yes.
```

---

## Prompt 1: heat, brightness, and the "could this be Mars" filter

```
Read CLAUDE.md and HANDOFF.md. Fetch and pull. Work on a branch named
feature/thermal.

Goal: the Nile Delta must stop matching Mars, while Atacama and Death Valley
keep matching. Right now the model only sees the shape of the ground, so it
cannot tell a flat Martian plain from flat farmland.

Add three things, each as its own function in a new src/surface.py.

A. A "could this be Mars" filter, Earth only.
   Mars has no plants and no surface water. Use Earth Engine (src/config.py,
   init_ee) to compute, per tile:
   - median NDVI over the last 3 years from MODIS (verify the dataset ID in
     the Earth Engine catalog, likely MODIS/061/MOD13A2)
   - fraction of permanent water from JRC Global Surface Water
   Mark a tile "Mars-possible" when median NDVI < 0.15 and water fraction
   < 5%. Tiles that fail are never offered as twins. Make the thresholds
   constants at the top of the file so we can explain and tune them.

B. How well the ground holds heat.
   - Earth: apparent thermal inertia, ATI = (1 - albedo) / (T_day - T_night),
     from MODIS land surface temperature (verify the ID, likely
     MODIS/061/MOD11A2) and MODIS albedo (likely MODIS/061/MCD43A3,
     white-sky shortwave). Use the median over 3 years.
   - Mars: the THEMIS night-time infrared mosaic (URL in
     docs/ENGINE_PROMPTS.md). Ground that stays bright at night holds heat:
     rock, crusts. Ground that goes dark is dust and fine sand. It is an
     8-bit qualitative product, not calibrated thermal inertia.
   The two are measured in different units, so do not compare raw values.
   Convert each to a percentile within its own world, and call the feature
   heat_rank. Write a short paragraph in HANDOFF.md explaining this choice
   honestly: it compares "how rocky is this place for its planet", and it is
   a stand-in because the quantitative THEMIS mosaic returns 404.

C. Brightness.
   - Earth: MODIS albedo as above.
   - Mars: TES albedo mosaic (URL in docs/ENGINE_PROMPTS.md).
   Also as a within-world percentile, called bright_rank.

Then extend terrain.report_cards so every tile carries mean_slope,
slope_spread, relief, heat_rank and bright_rank, plus mars_possible for
Earth. Rerun the Phase 1 comparison with the filter applied.

Success:
- Nile Delta under 5% of matches (unskip the placeholder test)
- Atacama plus Death Valley still at least 60%
- Make a second chart, figures/validation_with_heat.png, in the same style
  as validation_elevation_only.png, so the two sit side by side in the
  presentation.

If the Nile Delta does not drop, stop and show me the numbers before
changing anything. Do not tune thresholds just to pass the test.

Show me the results, the charts and the diff. Wait before committing.
```

---

## Prompt 2: the real target sites, and the Moon

```
Read CLAUDE.md and HANDOFF.md. Fetch and pull. Work on a branch named
feature/targets.

The challenge asks for analogs of "permanent Moon base locations and Mars".
So the targets should be the sites NASA itself has proposed, not ones we
picked.

A. Mars: NASA's candidate human Exploration Zones.
   The USGS archive has one CTX mosaic per proposed zone at
   https://asc-pds-services.s3.us-west-2.amazonaws.com/wms_basemaps/Mars/CTX_EZs/
   (list the bucket with ?list-type=2&prefix=wms_basemaps/Mars/CTX_EZs/).
   Each *_CTX_BlockAdj_dd.tif is one zone. Read only the georeferencing of
   each file, not the pixels, and build data/targets/mars_human_ez.csv with
   name, centre lat, centre lon and bounding box. Fix names from the file
   names (Gale, Jezero, Arcadia Planitia, ...). Check a few centres against
   known coordinates, for example Gale near 5.4S 137.8E.
   Commit this small CSV under src/targets/, not data/, since data/ is
   ignored and the team needs it.

B. Moon: Artemis III candidate landing regions near the south pole.
   Search the web for NASA's current official list and coordinates. As of
   late 2024 it was nine regions including Haworth, Malapert Massif,
   Mons Mouton, Nobile Rim and de Gerlache Rim, but check whether it has
   changed. Save src/targets/moon_artemis.csv with the source URL in a
   comment line.

C. Moon features.
   Add moon_patch() to terrain.py using the LOLA global DEM (URL in
   docs/ENGINE_PROMPTS.md, radius 1,737,400 m, same approach as
   mars_patch). The file is not tiled, so read small windows only.
   The south pole is a problem: an equirectangular map stretches badly
   there. Find a polar stereographic LOLA product for the south pole on
   NASA PGDA, verify it opens, and use that for any site south of 80S.
   Test on a known answer first: Shackleton crater rim near the pole and
   its floor depth around 4 km below the rim.
   For the Moon, start with terrain only. Moon thermal (Diviner) is a later
   upgrade, note it in HANDOFF.md.

D. Run every Mars zone and every Moon region through report_cards and save
   data/processed/targets_features.parquet.

Show me the two target CSVs, the Shackleton check and the diff. Wait before
committing.
```

---

## Prompt 3: score the whole Earth

```
Read CLAUDE.md and HANDOFF.md. Fetch and pull. Work on a branch named
feature/global-grid. Prompt 1 (feature/thermal) must be merged first.

Goal: one feature row for every land tile on Earth, about 9 km across to
match our Mars tiles (20 pixels x 463 m). This becomes the global
"how Mars-like is every place" map, the poster image of the project.

Use Earth Engine, because downloading global elevation would be terabytes.
- Compute slope from Copernicus DEM (verify the ID, likely
  COPERNICUS/DEM/GLO30) at about 90 m, then aggregate to a 9 km grid with
  reduceResolution for mean slope, slope standard deviation, and relief
  (max minus min elevation).
- Add the Earth layers from src/surface.py: heat, brightness, NDVI, water.
- Restrict to land between 85N and 85S. Include Antarctica, since the Dry
  Valleys are a known analog.

Quota matters. We are on the Community tier with a monthly compute limit
and no billing account. So:
- First run one continent, Africa, and tell me how much compute it used
  (the Tasks tab or the export's reported EECU usage).
- Estimate the cost of the rest before running it. If it looks like more
  than half the monthly quota, stop and propose a cheaper grid, for example
  only tiles that pass the Mars-possible filter.
- Export each continent as a table to Google Drive, then download into
  data/processed/earth_grid/. That folder is gitignored.

Then apply the same within-world percentile ranking as prompt 1, and save
data/processed/earth_grid.parquet.

Validation, which is the chart judges will remember most:
- Known analog sites: Atacama, Death Valley, Haughton Crater, Devon Island,
  McMurdo Dry Valleys, Mauna Kea, Iceland lava fields near Krafla, Utah
  near Hanksville (MDRS), Rio Tinto in Spain, Svalbard, Arkaroola in
  Australia, Black Point Lava Flow in Arizona, Meteor Crater. Look up and
  save their coordinates in src/targets/known_analogs.csv with sources.
- For each Mars target zone, rank every Earth tile by similarity. Report
  where the known analogs fall: their median percentile across all targets.
- If the known analogs sit in the top 10% of all Earth land, that is our
  headline result. Draw figures/known_analogs_rank.png.

Show me the compute used, the validation numbers and the chart. Wait before
committing.
```

---

## Prompt 4: the discoveries list, and the data the interface reads

```
Read CLAUDE.md and HANDOFF.md. Fetch and pull. Work on a branch named
feature/discoveries. Prompts 2 and 3 must be merged first.

A. Similarity scores.
   For every target (Mars zones and Moon regions) and every Mars-possible
   Earth tile, compute a similarity score from 0 to 100, standardized the
   same way as before. Also keep, per match, how close each single feature
   is, so the interface can show "why this matches" bars (slope 92%,
   heat 87% and so on).

B. Discoveries.
   - Drop Earth tiles within 50 km of a known analog in
     src/targets/known_analogs.csv. We want places nobody uses yet.
   - Merge top tiles closer than 100 km into one candidate site.
   - Add the nearest city of 100,000+ people and the straight-line
     distance, from the free GeoNames cities15000 file or Natural Earth
     populated places. Record the source.
   - Rank and keep the top 10 for Mars and the top 5 for the Moon.
   - For each, write two plain-language sentences: what it matches well,
     and what it does not match. Be honest about the mismatch.
   - Also report the best site inside Egypt, even if it is not in the
     top 10, since we plan to visit and photograph it.

C. Data for the interface.
   Write small JSON files to web/public/data/, which is committed:
   - targets.json: every Mars and Moon target with coordinates
   - matches/<target_id>.json: top 25 Earth matches with score, coordinates
     and per-feature closeness
   - discoveries.json: the top lists from B
   - earth_grid_mars_score.png or a compact tiled version for the global map
   Keep the total under 20 MB so the site loads fast and works offline.

D. Reverse mode data: for a list of 50 major world cities including Cairo,
   precompute the nearest Earth tile with a score above 70 for each Mars
   target, and its distance.

Show me the discoveries list first, before writing the JSON, so we can
sanity check it together. Wait before committing.
```

---

## Prompt 5 (optional): image AI

```
Read CLAUDE.md and HANDOFF.md. Fetch and pull. Work on a branch named
feature/vision.

Goal: a second, independent engine that compares what terrain looks like,
not its numbers. Where both engines agree, the match is stronger.

Important design rule: compare like with like. Satellite photos of Earth and
orbital photos of Mars differ in colour, lighting and camera, so the AI would
learn the camera, not the ground. Instead, render a hillshade from the
elevation data of both worlds, at the same pixel size (463 m), the same sun
angle (315 azimuth, 45 elevation) and the same tile size, so the only
difference left is the shape of the land.

- Add hillshade rendering to terrain.py.
- Use DINOv2 small (facebook/dinov2-small) to turn each tile into an
  embedding. Put torch and transformers in a separate environment file,
  environment-vision.yml, so the main environment stays light. If the
  laptop is too slow, write it as a Google Colab notebook in notebooks/.
- Embed the Mars target tiles and the top 200 Earth tiles from the physical
  engine for each target. Compute cosine similarity.
- Report, per target, how often the two engines agree on the top 10.
- Save a figure with three Mars tiles next to their best visual twin on
  Earth, figures/vision_pairs.png.

Show me the agreement numbers and the figure. Wait before committing.
```
