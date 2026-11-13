# What the chatbot knows about the project

This file is sent to Gemini as background for every conversation (see
`src/chatbot.py`). Keep it short, factual and in step with `HANDOFF.md`.
Specific scores, places and ranks are NOT written here: the bot looks them
up in `web/public/data/` with tools, so they always match the website.

## The project

Planetary Twin Finder finds places on Earth whose ground best matches the
sites NASA has proposed for crewed landings and bases on Mars and the Moon.
Built by computer science students at Egyptian Chinese University, Cairo, for
the NASA Space Apps Challenge 2026, challenge "Identify Earth Locations that
Analog the Permanent Moon Base Locations and Mars". Mission teams train at a
handful of Earth analogs (mostly the Atacama Desert, Haughton Crater and
Death Valley); the tool searches whole continents with data to find more,
including ones nearer and cheaper to reach.

## Targets: NASA's own sites, not ours

- Mars: NASA's 38 candidate human Exploration Zones, located from the USGS
  CTX Exploration Zone mosaics.
- Moon: the nine Artemis III candidate landing regions near the lunar south
  pole announced in October 2024 (outlines from USGS data release DOI
  10.5066/P1MEQ6UK, checked against NASA's own table). Artemis III has since
  become an Earth-orbit test flight; the first crewed landing is now
  Artemis IV, whose site NASA has not chosen.

## Method (called V1)

- Every world is cut into tiles of 20 x 20 pixels of 463 m (about 9.3 km),
  the pixel size of the Mars elevation map. Earth and Moon elevation are
  averaged down to 463 m the same way Mars's pixels were made, so no world
  looks rougher just because of its data.
- Each tile gets a "report card": mean slope, slope spread (roughness),
  relief (highest minus lowest point), and for Mars and Earth, albedo
  (brightness, 0 to 1).
- Earth tiles must be "Mars-possible" to be offered at all: median NDVI below
  0.15 (almost no plants) and under 5% permanent water.
- Features are standardized (z-scores), and an Earth tile's distance to a
  site is its mean distance to the site's 10 most similar tiles, so a twin
  only has to resemble part of a site (a crater floor, say).
- Score = 100 x exp(-distance / 0.4). Only the ranking matters; the score is
  a readable label. Each twin also has a rank among all ranked Earth tiles.
- Listed twins are at least 25 km apart, so they are different places.
- Heat (thermal inertia) is not used for matching: on Earth the available
  measure mostly tracks soil moisture, on Mars rock versus dust, so the two
  are not comparable. It only labels Mars tiles dusty, sandy or rocky.

## Data sources

- Mars elevation: MOLA global DEM, 463 m (NASA Mars Global Surveyor, via
  USGS Astropedia, from the Planetary Data System).
- Mars brightness: TES albedo (Mars Global Surveyor). Mars night infrared:
  THEMIS (Mars Odyssey), for labels only.
- Moon elevation: LOLA south pole DEM, 80 m (Lunar Reconnaissance Orbiter,
  NASA PGDA, Barker et al. 2023).
- Earth elevation: Copernicus DEM GLO-30 (ESA), from AWS Open Data.
- Earth vegetation and brightness: NASA MODIS (MOD13C1 NDVI, MCD43C3 albedo);
  permanent water: JRC Global Surface Water. Processed with Google Earth
  Engine under a strict compute cap.

## Validation

- Blind test: the model was never told which places NASA already uses. With
  V1, Atacama and Death Valley took 92.5% of all Mars matches against four
  Earth test regions (73% with elevation alone).
- A control, the Nile Delta (green farmland), is removed by the Mars-possible
  filter; what little still matches is desert east of Cairo inside the same
  test box.
- A first attempt, ranking heat and brightness as percentiles within each
  world, failed (the Nile Delta rose to 29% of matches) and was dropped. The
  team published this rather than hiding it.
- Known-answer checks: Olympus Mons height from MOLA, Shackleton crater depth
  from LOLA (4.06 km measured, about 4.2 km published).

## Findings worth knowing

- The Mars sites have albedo about 0.15 to 0.22, while most Earth desert is
  brighter, so the best twins tend to be dark, often volcanic or basaltic
  ground. Jezero's best twins include dark ground in Egypt's Eastern Desert,
  inland from the Red Sea.
- The lunar south pole is far rougher than almost any dry land searched; only
  volcanic mountains come close (for example Tibesti in Chad, Afar in
  Djibouti, the Atlas in Morocco).

## Limits (say these honestly when relevant)

- Moon sites are matched on terrain only: there is no Moon brightness layer
  yet. Moon scores are low (best about 15) and must not be compared with Mars
  scores; the rank (for example 1 of 130,060) is the meaningful number.
  Planned upgrades: LRO Diviner thermal data and LOLA albedo.
- Earth and Mars brightness come from different instruments and
  atmospheres, so small brightness differences mean little.
- Only the continents listed in the conversation's coverage note have been
  searched so far; the best twin anywhere on Earth may lie elsewhere.
- No twin has been checked on the ground yet; scores describe terrain shape
  and brightness at 9 km scale, not rocks, chemistry or temperature.
