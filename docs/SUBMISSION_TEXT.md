# Space Apps project page: text to paste

One section per field of the global project page (order and questions from
the official *Project Submission Guide*, 13 November 2026). Paste each block
into its field as plain text. Every number here was checked against
`web/public/data/` on 14 November 2026.

**Before pasting, check three things:**

1. **Demo link:** upload `video/planetary-twin-finder-30s.mp4` (29.5 s) to
   YouTube as *Unlisted* or *Public*, then paste its link. Open it in a
   private window to be sure it plays without a login.
2. **GitHub link:** make `maroo2007/analog-finder` public first, or remove
   that line.
3. **Use of AI:** the guide says AI must not be used to come up with the
   idea. The text says the idea and the method's decisions are the team's;
   make sure that is how you would describe it.

---

## Project Name

Planetary Twin Finder

---

## High-Level Project Summary

Planetary Twin Finder finds the places on Earth whose ground best matches the
sites NASA has proposed for landing humans on Mars and the Moon. Astronauts
and rovers rehearse at a handful of Earth analogs, chosen mostly by field
experience. We compared the whole dry planet instead. Every patch of ground
on Earth, Mars and the Moon is described with the same four numbers (slope,
roughness, relief and brightness) at the same 463 m pixel size as NASA's Mars
elevation map. Earth ground with plants, water or ice is removed, and each
NASA site gets a ranked, explained list of its closest Earth twins. In a
blind test, without being told where NASA trains, 92.5% of our Mars matches
landed in the Atacama Desert and Death Valley, NASA's best-known analogs. The
method also found new ones: Jezero crater's closest twin, #1 of 148,925 dry
places in Africa and the Americas, is in Egypt's Eastern Desert. Mission
planners, field-test teams and students can use the website to find nearer,
cheaper and more varied places to rehearse for the Moon and Mars.

---

## Link to Project Demo

(paste the YouTube link here)

A 29.5 second video with English narration and English subtitles.

---

## Link to Final Project

https://duplicaa.vercel.app

Source code: https://github.com/maroo2007/analog-finder

---

## Detailed Project Description

**What it does**

The website has two parts. A scroll story explains the problem, the method
and the results. The Twin Finder lets anyone pick one of NASA's 47 proposed
landing sites (the 38 candidate human Exploration Zones on Mars and the nine
Artemis III candidate regions at the lunar south pole) and see its 25
closest twins on Earth on a satellite map. Each twin card shows its score,
its rank among all dry places on Earth and within its continent, how close
each of the four features is, a side-by-side shaded relief of the target and
the twin, what Earth cannot copy (for the Moon, Diviner temperatures and
ice-stability shares), and links to Google Maps, NASA Worldview and the
Copernicus Browser to check the place with your own eyes. An "Ask the
analyst" panel answers questions about the result on screen, using only our
data.

**How it works**

1. Every world is cut into tiles about 9.26 km across (20 x 20 pixels of
   463 m, the resolution of NASA's MOLA map of Mars). Earth and Moon
   elevation are averaged down to the same pixel size, so all three worlds
   are measured the same way.
2. Each tile gets four numbers: mean slope, slope spread (roughness),
   relief (highest minus lowest point) and albedo (brightness).
3. On Earth, a tile is kept only if it could look like Mars: median NDVI
   below 0.15 (no plants), under 5% permanent water, and under 50% permanent
   snow and ice. That leaves 148,925 dry tiles in Africa and the Americas
   south of 50 N (130,060 in Africa).
4. Features are standardized together, and each Earth tile's distance to a
   NASA site is its mean distance to the site's 10 nearest tiles. The score
   is 100 x exp(-distance / 0.4), so 100 is a perfect match. Twins in a list
   are at least 25 km apart.
5. The Moon is matched on terrain only, with its own scaler, because there
   is no comparable brightness data yet. Its scores (best 5 to 33) are much
   lower than Mars scores (best 63 to 98), because the lunar south pole is
   rougher than almost any dry land, so the site shows ranks rather than
   scores for the Moon.

**How we know it works**

We tested the method blind. Without telling it where NASA trains, 92.5% of
its Mars matches fell in the Atacama Desert and Death Valley; a wet farmland
control box (the Nile Delta) got 7.5%, and those were desert tiles east of
Cairo, not farmland. We also kept the failures: adding heat as a feature
dropped the result to 84.3% (on Earth, day-night temperature mostly measures
soil moisture; on Mars it measures rock versus dust), and ranking by
percentiles within each world let the farmland control rise to 28.3%. Known
answers check the terrain code: Shackleton crater comes out 4.06 km deep
(published 4.2 km).

**Benefits**

- Mission teams can shortlist new analog sites from data, then visit only
  the best ones.
- Countries without a famous analog can find their own: Egypt's Eastern
  Desert is the closest twin of Jezero crater, where Perseverance landed.
- Every result is explained, feature by feature, and every limit is stated,
  so it is a starting point for field teams, not a black box.

**Limits, stated honestly**

Matching uses terrain shape and brightness at about 460 m: no rock
chemistry, no temperature, no boulders. The Earth grid covers Africa and the
Americas south of 50 N so far. The Moon has no brightness feature yet, and
its polar lighting and permanent cold have no Earth equivalent. The results
are a ranked shortlist, not a substitute for visiting a site.

**What we hope to achieve**

Cover the rest of the world, add a brightness feature for the Moon (LOLA
albedo), add a second, image-based engine, and add a reverse mode that finds
the nearest good twin to any city, so a university or space agency can find
a place to train close to home.

**Tools and languages**

Python 3.11 (rasterio, GDAL, GeoPandas, NumPy, pandas, scikit-learn,
matplotlib, pytest), Google Earth Engine for the MODIS and water layers,
JavaScript with Vite, three.js, MapLibre GL JS, GSAP and Lenis for the
website, Google Gemini for the analyst panel, hosted on Vercel.

---

## Use of Super Intelligence (SI)

Yes. The project idea and the method's decisions are the team's. We used
Claude (Anthropic), through Claude Code, as a programming assistant to help
write the data pipeline, the tests, the website and our documents; we
checked every number against our own data files. The website's "Ask the
analyst" panel uses Google Gemini; it is labelled as AI on screen and
answers only from our data. In the demo video, the English narration is an
AI-generated voice (HeyGen stock voice "Annie") reading a script the team
wrote with Claude, and the background music was composed and synthesised in
code by Claude, with no samples or recordings; both are acknowledged in the
video file's metadata and on this page. No image or video in the project is
AI-generated: the footage is screen capture of our own website, and no NASA
logos or branding are used.

---

## NASA Data

- **MOLA** elevation (Mars Global Surveyor), 463 m, from the NASA Planetary
  Data System via USGS Astropedia: slope, roughness and relief for Mars.
- **TES** albedo (Mars Global Surveyor), via USGS Astropedia: Mars
  brightness.
- **NASA's 38 candidate human Exploration Zones** on Mars, located from the
  USGS CTX Exploration Zone mosaics: the Mars targets.
- **LOLA** south pole elevation model, 80 m (Lunar Reconnaissance Orbiter;
  NASA PGDA, Barker et al. 2023): Moon terrain.
- **LRO Diviner** south Polar Resource Product (Paige et al. 2010, PDS
  Geosciences Node): Moon temperatures, cold-trap and ice-stability shares,
  shown as context on each Moon card.
- **NASA's nine Artemis III candidate regions** (October 2024), outlines
  from USGS (DOI 10.5066/P1MEQ6UK), checked against NASA's own table (NTRS
  20250007692): the Moon targets.
- **MODIS** vegetation (MOD13C1, MOD13A2), albedo (MCD43C3, MCD43A3) and
  land cover (MCD12Q1), from NASA Earthdata via Google Earth Engine: the
  no-plants and no-ice filters and Earth brightness.
- **NASA GIBS** imagery in the map (Blue Marble, Landsat WELD, ASTER GDEM
  relief, reference labels), and links to **NASA Worldview** from every
  twin.
- **Blue Marble Next Generation** (NASA Earth Observatory) and the **NASA
  Scientific Visualization Studio CGI Moon Kit** for the globes, and the
  Viking colour mosaic of Mars (NASA/JPL/USGS).

---

## Space Agency Partner Data and Other References

**Space Agency Partner data (ESA)**

- **Copernicus DEM GLO-30** (ESA, via AWS Open Data): all Earth terrain.
  Produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus
  Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European
  Union and ESA; all rights reserved. The organisations in charge of the
  Copernicus programme by law or by delegation do not incur any liability
  for any use of the Copernicus WorldDEM-30.
- **Copernicus Data Space Ecosystem**: every twin card links to the
  Copernicus Browser.
- **EOxCloudless Sentinel-2** map layer by EOX IT Services GmbH (contains
  modified Copernicus Sentinel data 2025), CC BY-NC-SA 4.0.

**Other data**

- JRC Global Surface Water (European Commission Joint Research Centre), via
  Google Earth Engine: the permanent-water filter.
- USGS: CTX Exploration Zone mosaics, Artemis III region outlines (DOI
  10.5066/P1MEQ6UK) and SRTM in the terrain tiles.
- LROC QuickMap (Arizona State University), from which the Artemis region
  outlines were drawn.
- Terrain Tiles on AWS Open Data (Mapzen; SRTM, U.S. Geological Survey;
  ETOPO1, U.S. NOAA; and others).
- © OpenStreetMap contributors (map layer).

**Papers**

- Barker, M. K. et al. (2023), LOLA south pole digital elevation models,
  NASA PGDA, doi:10.60903/gsfcpgda-lola-spole.
- Paige, D. A. et al. (2010), Diviner Lunar Radiometer observations of cold
  traps in the Moon's south polar region, *Science* 330, 479,
  doi:10.1126/science.1187726.

**Software, type and media**

- three.js, MapLibre GL JS, GSAP, Lenis and Vite (website); rasterio, GDAL,
  GeoPandas, NumPy, pandas, scikit-learn and matplotlib (data pipeline);
  Google Earth Engine; Google Gemini (analyst panel); Vercel (hosting);
  ffmpeg (video editing).
- Archivo typeface (SIL Open Font License).
- Loading animation by ZacharyCrespin on Uiverse.io (MIT licence).
- Design review with the Impeccable skill by Paul Bakaus (Apache 2.0).
- Demo video: footage is screen capture of our own website; narration by
  HeyGen (stock voice "Annie"); music synthesised in our own code.

The website is not affiliated with or endorsed by NASA, ESA or any other
agency, and shows no agency logos.
