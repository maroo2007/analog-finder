# Engine prompts for Claude Code

Written 10 October 2026. Paste each prompt into Claude Code, one at a time, on
the laptop that holds the repo. Each one ends with Claude Code stopping for
your approval, so nothing gets committed without you seeing it.

Order:

| # | What | Depends on | Who |
|---|---|---|---|
| 0 | Save Phase 1, set up the test suite | nothing | done 10 Oct |
| 1 | Heat, brightness, and the "could this be Mars" filter | 0 | done 10 Oct |
| 2 | Real target sites: NASA's Mars landing zones and Artemis Moon regions | 0 | done 13 Nov (`docs/PROMPT_targets_moon.md`) |
| 3 | Score the whole Earth | 1 | Earth person |
| 4 | Discoveries list and the data the interface reads | 2 and 3 | either |
| 5 | Image AI (optional) | 0 | anyone with spare time |

Prompts 1 and 2 can run at the same time on two laptops, each on its own
branch.

Data sources below were checked on 10 October and all open with no key:

- Mars elevation: `planetarymaps.usgs.gov/mosaic/Mars_MGS_MOLA_DEM_mosaic_global_463m.tif`
- Mars brightness: `planetarymaps.usgs.gov/mosaic/Mars_MGS_TES_Albedo_mosaic_global_7410m.tif`
- Mars night-time infrared, 60N to 60S, 100 m, no overviews (read small
  windows only; one site window is about 3 MB):
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

## Prompt 1: heat, brightness, and the "could this be Mars" filter (done)

Done on 10 October 2026, branch `feature/thermal`. The method we actually
used differs from the original prompt, which asked for heat and brightness
as percentiles within each world. That failed: the Nile Delta box rose from
13% to 29% of Mars matches, because the Mars sites are typical Mars while
Earth's analogs are extreme Earth. The full story is in `HANDOFF.md`
section 7.

The method in use, called V1:

- **Mars-possible filter**, Earth only (`src/surface.py`): median NDVI over
  2023 to 2025 below 0.15 (MODIS/061/MOD13A2) and under 5% permanent water
  (JRC/GSW1_4 seasonality = 12). Tiles that fail are never offered as twins.
- **Absolute albedo**, both worlds, in physical units 0 to 1: Earth MODIS
  white-sky shortwave albedo (MODIS/061/MCD43A3), Mars TES albedo. No
  percentiles. Different instruments and atmospheres, so small differences
  mean little.
- **Terrain** as in Phase 1: mean slope, slope spread, relief.
- **Heat is not a matching feature.** On Earth the stand-in (apparent thermal
  inertia from MODIS) mostly measures moisture; on Mars THEMIS night infrared
  measures rock versus dust. It is computed only to label Mars tiles dusty,
  sandy or rocky. Earth tiles get no label. V2 (V1 + heat, Earth ranked
  against bare dry land) stays available with
  `python src/run_thermal.py --with-heat`.

Result: Atacama and Death Valley take 92.3% of Mars matches. The filter
removes 79% of the Nile Delta box; its remaining 7.7% comes from desert
east of Cairo. Charts: `figures/validation_elevation_only.png` and
`figures/validation_with_heat.png`. Tests: `tests/test_validation.py`.

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

Use the V1 method from prompt 1, exactly: terrain + absolute albedo + the
Mars-possible filter. No heat, and no within-world percentiles anywhere.
Read src/surface.py and src/run_thermal.py first and reuse their constants
(NDVI_MAX, WATER_MAX, DATE_START, DATE_END) so the grid matches the
validated method.

Status, 12 October 2026: built as src/earth_grid.py, which differs from the
plan below because the first Africa export burned 14.7 EECU-hours (see
HANDOFF.md section 7). Earth Engine does only coarse NDVI (MOD13C1) for
every land tile, then water (JRC) and albedo (MCD43C3) for tiles that pass
NDVI, each export under a cost cap. Terrain is computed on the laptop from
the Copernicus DEM on AWS, with terrain.earth_patch (average resampling)
and report_cards, so the grid uses exactly the validated code. Egypt and
Africa are done; run other areas with:
    python src/earth_grid.py run <area> --cap <EECU-hours>
after adding the area to AREAS and estimating its cost from a similar
country first.

Original plan:
- Terrain: resample Copernicus DEM (verify the ID, likely
  COPERNICUS/DEM/GLO30) to 463 m first, the same pixel size as MOLA, and
  only then compute slope. Slope depends on pixel size, so computing it at
  90 m would make Earth look rougher than Mars for no real reason. Then
  aggregate to the 9.26 km grid for mean slope, slope standard deviation,
  and relief (max minus min elevation).
- Albedo: median MODIS white-sky shortwave albedo (MCD43A3), in physical
  units 0 to 1, as in surface.earth_layers.
- Filter: median NDVI and permanent-water fraction, as in surface.py. Keep
  them as columns and a mars_possible flag; only Mars-possible tiles are
  ever offered as twins.
- Restrict to land between 85N and 85S. Include Antarctica, since the Dry
  Valleys are a known analog.

Targets need the same features. Mars zones: terrain from MOLA plus TES
albedo (surface.mars_albedo). Moon regions: terrain only, since there is no
Moon albedo source yet; say so wherever Moon matches are shown.

Quota matters. We are on the Community tier with a monthly compute limit
and no billing account. So:
- First run one continent, Africa, and tell me how much compute it used
  (the Tasks tab or the export's reported EECU usage).
- Estimate the cost of the rest before running it. If it looks like more
  than half the monthly quota, stop and propose a cheaper grid, for example
  only tiles that pass the Mars-possible filter.
- Export each continent as a table to Google Drive, then download into
  data/processed/earth_grid/. That folder is gitignored.

Save data/processed/earth_grid.parquet. Match with the same
standardization as run_thermal.match (z-scores fitted on targets and Earth
tiles together), not percentiles.

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

Egypt: report the best Egyptian tiles for each Mars target. We do not
hand-pick the Egypt site; this list chooses it. Expect dark ground: the
Mars sites have albedo 0.15 to 0.22, while most Earth desert is brighter,
so the best twins should be dark, basaltic ground.

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
   albedo 87% and so on). Heat is not a matching feature; Mars tiles may show
   a dusty, sandy or rocky label, Earth tiles never.

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
