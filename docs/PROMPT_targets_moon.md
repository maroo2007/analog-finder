Read CLAUDE.md and HANDOFF.md first, then docs/ENGINE_PROMPTS.md (Prompt 2).
Fetch and pull as CLAUDE.md says, and work on a new branch named
feature/targets made from the latest main.

Context: the hackathon is 14 to 15 November. The registration video and
proposal are done. We are back on the engine.

PART 1: save work that is not in git yet

A Claude session in the cloud built these, and I copied them into the
project folder. Nothing here is committed yet. Read every file before running
anything (a judge may ask how it works).

- src/targets/mars_human_ez.json
  NASA's candidate human Exploration Zones on Mars: 38 zones with id, name,
  centre and bounding box, taken from the georeferencing of the USGS CTX_EZs
  mosaics, duplicates removed. This replaces part A of Prompt 2.
- src/run_mars_targets.py
  Profiles every zone with the V1 features and writes
  data/processed/mars_ez_v1.parquet. That parquet is already in place (made
  in the cloud), so you don't have to re-run it unless you want to check it.
- src/build_web_data.py
  V1 matching of every zone against the Mars-possible Africa grid. Writes
  web/public/data/: targets.json, matches/<id>.json (top 25 twins, at least
  25 km apart), egypt.json (best Egyptian tile per zone), likeness.png/json.
  Score = 100 * exp(-distance / 0.4).
- src/render_shades.py
  Shaded relief thumbnails of each zone and its top twins
  (web/public/data/shade/).
- web/public/data/ and web/public/img/mars.jpg (Viking colour mosaic,
  NASA/JPL/USGS, public domain): the outputs, about 5 MB.

Do this:
1. Run python src/build_web_data.py and check it reproduces the files in
   web/public/data/ (same zones, same top twins). Sanity check: Jezero's
   best twin in Africa should be in Egypt's Eastern Desert near 25.13 N,
   34.54 E.
2. Add tests under tests/ for the parts that can break quietly: the score
   and closeness functions, the 25 km spacing between twins, and that
   targets.json has 38 zones with valid coordinates.
3. web/public/data/ is meant to be committed (Prompt 4 says so; it is small
   and the website needs it). data/ stays ignored as always.
4. Ignore data/_to_delete/: leftovers from copying, safe for me to delete.

Show me the diff and wait before committing.

PART 2: the Moon (parts B, C and D of Prompt 2)

B. Search the web for NASA's current official list of Artemis III candidate
   landing regions near the lunar south pole, with coordinates. As of late
   2024 it was nine regions (Peak near Cabeus B, Haworth, Malapert Massif,
   Mons Mouton Plateau, Mons Mouton, Nobile Rim 1, Nobile Rim 2, de Gerlache
   Rim 2, Slater Plain); check whether it has changed. Save
   src/targets/moon_artemis.json in the same format as mars_human_ez.json,
   with the source URL recorded.

C. Add moon_patch() to terrain.py.
   - The regions are all south of 80 S, where an equirectangular map is
     badly stretched, so use a polar stereographic LOLA south pole DEM from
     NASA PGDA. Verify it opens and read small windows only.
   - Average the elevation to 463 m pixels (Resampling.average), the same
     pixel size as Mars and Earth, so a tile is the same 20 x 20 pixels and
     the features are comparable.
   - Test on a known answer first: Shackleton crater, rim near the pole,
     floor about 4 km below the rim.
   - Terrain only for the Moon (slope, roughness, relief). There is no
     albedo feature for the Moon yet; note Diviner thermal and LOLA albedo as
     later upgrades in HANDOFF.md.

D. Profile every Artemis region and match it against the Mars-possible
   Africa grid with the three terrain features only (same standardization
   idea, same score formula). Extend build_web_data.py so targets.json holds
   both worlds (a "world" field: "mars" or "moon") and matches/<id>.json and
   egypt.json cover the Moon regions too.

Show me: the Artemis list with its source, the Shackleton check, the top 5
Earth twins for three Moon regions, and the diff. Wait before committing.

PART 3: when I approve

Commit Part 1 and Part 2 as separate commits, push feature/targets and open
a pull request. Update the "Where we are" section of CLAUDE.md and HANDOFF.md
section 7 with what changed.

Every Earth Engine task still needs a cost cap through earth_grid.run_capped,
but nothing in this prompt should need Earth Engine at all. If it seems to,
stop and tell me why first.
