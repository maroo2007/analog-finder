# Submission draft: Space Apps project page

Drafted 14 November 2026 for the team's project page (spaceappschallenge.org,
My Team, Project tab). Every number is from `HANDOFF.md` and the website
data. Every link below was checked and opened on 14 November, except the two
GitHub links, which GitHub refused to automated checks. Submission closes
**Sunday 15 November, 11:59 p.m. Cairo time**; only the last "Submit for
Judging" counts. Rules: `docs/JUDGING_CRITERIA.md`.

---

## Project Name

> Planetary Twin Finder

(The page currently says "Project Duplica". Duplica is the team name; the
project's name everywhere else, including the website, is Planetary Twin
Finder.)

## Summary (50 to 200 words; about 170 here)

> Planetary Twin Finder finds the places on Earth whose ground best matches the sites NASA has proposed for landing humans on Mars and the Moon. Astronauts and equipment are tested at a few Earth analog sites chosen mostly by experience. Instead, we give every 9 km patch of ground on Earth, Mars and the Moon the same profile, measured at the same 463 m pixel size from open NASA and ESA data: slope, roughness, relief and brightness. We remove Earth ground with plants, water or ice, then rank the closest Earth twins for NASA's 38 candidate Mars Exploration Zones and nine Artemis III Moon regions. The method was blind-tested: without being told about them, it sent 92.5% of Mars matches to the Atacama Desert and Death Valley, places NASA already uses. It also found something new: the closest twin of Jezero crater, where Perseverance landed, is in Egypt's Eastern Desert, #1 of 148,925 dry tiles in Africa and the Americas. Our Twin Finder website lets anyone explore every match, with honest notes on what Earth cannot copy.

## Project Demonstration

Not made yet. A video of **30 seconds or less** (English, or Arabic with
English subtitles) or **at most 7 slides including the title and intro**,
on YouTube or Google Drive, shared so anyone with the link can open it.
Paste the full URL, starting with `https://`.

## Project

> https://duplicaa.vercel.app

(The Twin Finder itself is https://duplicaa.vercel.app/explorer.html, linked
from the story page.)

## Project Details

> **What it does.** Planetary Twin Finder ranks the places on Earth whose terrain best matches NASA's own proposed human landing and base sites: the 38 candidate Exploration Zones on Mars and the nine Artemis III candidate regions near the lunar south pole. The website has two parts: a scroll story that explains the idea for anyone, and the Twin Finder, where you pick a Mars or Moon site and see its 25 closest Earth twins on a satellite map, each with a shaded-relief image beside the target, its rank, a closeness bar for each feature, what Earth cannot copy, and links to Google Maps, NASA Worldview and the Copernicus Browser. An Egypt tab lists the best Egyptian site for every target. "Ask the analyst" (Google Gemini, labelled as AI) answers questions only from the data on screen, in English or Arabic.
>
> **How it works.** Every world is cut into tiles 9.26 km across, made of 20 x 20 pixels at 463 m, the resolution of NASA's MOLA map of Mars. Earth (Copernicus DEM) and Moon (LRO LOLA) elevation are averaged down to the same pixel first, because MOLA pixels are averages; sampling instead made Earth look 6 to 9% rougher. Each tile gets four numbers: mean slope, roughness (slope spread), relief and brightness (albedo: TES for Mars, MODIS for Earth). Earth tiles must be "Mars-possible": almost no vegetation (MODIS NDVI below 0.15), under 5% permanent water (JRC) and under 50% permanent ice (MODIS land cover). Features are standardized, a tile's distance to a target is its mean distance to the target's 10 nearest tiles, and twins are listed at least 25 km apart. The grid covers Africa and the Americas south of 50 N: 148,925 Mars-possible tiles. Earth Engine work ran under strict compute caps on the free tier; terrain was computed on our own laptops.
>
> **Does it work?** We blind-tested the method: it was never told which places NASA uses. With terrain, the Mars-possible filter and brightness, 92.5% of all Mars matches went to the Atacama Desert and Death Valley, two of NASA's best-known analog sites (73% with elevation alone). A control, the green Nile Delta, is removed by the filter. We also tried and rejected two ideas and kept the record: heat as a feature (on Earth it mostly measures soil moisture, on Mars rock versus dust) and ranking features within each planet, which made the farmland control rise to 29%. Known-answer checks: Olympus Mons' height from MOLA, Shackleton crater's depth from LOLA (4.06 km measured, about 4.2 km published).
>
> **What we found.** Jezero crater's closest Earth twin is dark ground in Egypt's Eastern Desert, inland from the Red Sea (25.125 N, 34.54 E): #1 of 148,925 tiles, ahead of the Atacama and Death Valley. Mars sites are darker than most Earth deserts, so the best twins are dark, often volcanic ground. The lunar south pole is rougher than almost any dry land; its closest twins are mostly in the Andes. Moon regions also show NASA LRO Diviner temperatures, cold-trap and ice-stability shares as context.
>
> **Benefits and impact.** Mission teams get a ranked, explained shortlist of new test sites for each specific NASA target, including sites nearer and cheaper to reach than the usual few, like Egypt's. The same method works for any new target or any part of Earth. It also opens planetary science to the public, and to Egyptian students in particular, who can see a piece of Mars in their own country.
>
> **Honest limits.** No place on Earth copies Mars or Moon gravity, air or radiation. Tiles are 9 km averages, so rocks, boulders and chemistry are not compared. The Moon is matched on terrain only (no brightness layer yet), so its scores are low and not comparable with Mars; we show its rank instead. Only Africa and the Americas south of 50 N are scored so far, and no twin has been visited yet. The results are a shortlist for field teams, not a replacement for a visit.
>
> **Tools.** Python (rasterio, GDAL, NumPy, pandas, scikit-learn, geopandas), Google Earth Engine, AWS Open Data; the website in JavaScript with Vite, three.js, MapLibre GL JS, GSAP and Lenis, hosted on Vercel, with one server function calling Google Gemini.

## Use of Super Intelligence (SI)

Select the options for **code**, **text and documents**, and **an AI
feature inside the project** (chatbot / large language model), if the list
has them. Do **not** select images, video or audio: none of ours are
AI-generated. The website's credits already say this in its "How we used AI"
line, which is what judges can see:

> Claude (Anthropic) helped write the data pipeline, this website and our documents; we checked the numbers against our own data files. The Twin Finder's "Ask the analyst" uses Google Gemini, is labelled as AI and answers only from the data on screen. No image or video here is AI-generated.

If the form has a free-text box, paste that line. The rules also ask for AI
code to be acknowledged in metadata: the commit messages in the repository
carry Claude co-author lines.

## NASA Data (Link Text, Link URL)

| Link Text | Link URL |
|---|---|
| MOLA global elevation, 463 m (Mars Global Surveyor) | https://astrogeology.usgs.gov/search/map/mars_mgs_mola_dem_463m |
| TES albedo (Mars Global Surveyor) | https://astrogeology.usgs.gov/search/map/mars_mgs_tes_albedo_mosaic_global_7410m |
| Viking global colour mosaic of Mars | https://astrogeology.usgs.gov/search/map/mars_viking_global_color_mosaic_925m |
| NASA Mars human Exploration Zones (First Landing Site / Exploration Zone Workshop) | https://www.hou.usra.edu/meetings/explorationzone2015/pdf/program.pdf |
| Exploration Zone CTX mosaics (USGS) | https://asc-pds-services.s3.us-west-2.amazonaws.com/?list-type=2&prefix=wms_basemaps/Mars/CTX_EZs/ |
| NASA Planetary Data System | https://pds.nasa.gov/ |
| LRO LOLA south pole elevation (NASA PGDA, Barker et al. 2023) | https://doi.org/10.60903/gsfcpgda-lola-spole |
| NASA Lunar Reconnaissance Orbiter data (PDS Geosciences) | https://pds-geosciences.wustl.edu/missions/lro/ |
| LRO Diviner Polar Resource Product (PDS Geosciences) | https://pds-geosciences.wustl.edu/missions/lro/diviner.htm |
| NASA Artemis III candidate landing regions | https://www.nasa.gov/news-release/nasa-provides-update-on-artemis-iii-moon-landing-regions/ |
| NASA SVS CGI Moon Kit (globe textures) | https://svs.gsfc.nasa.gov/4720 |
| MODIS vegetation index MOD13C1 | https://doi.org/10.5067/MODIS/MOD13C1.061 |
| MODIS vegetation index MOD13A2 (validation) | https://doi.org/10.5067/MODIS/MOD13A2.061 |
| MODIS albedo MCD43C3 | https://doi.org/10.5067/MODIS/MCD43C3.061 |
| MODIS albedo MCD43A3 (validation) | https://doi.org/10.5067/MODIS/MCD43A3.061 |
| MODIS land cover MCD12Q1 (ice filter) | https://doi.org/10.5067/MODIS/MCD12Q1.061 |
| NASA Earthdata | https://www.earthdata.nasa.gov/ |
| NASA Worldview | https://worldview.earthdata.nasa.gov/ |
| NASA GIBS imagery (Blue Marble, Landsat WELD, ASTER GDEM relief) | https://nasa-gibs.github.io/gibs-api-docs/ |
| Blue Marble Next Generation (NASA Visible Earth) | https://visibleearth.nasa.gov/collection/1484/blue-marble |

## Space Agency Partner & Other Data (Link Text, Link URL)

| Link Text | Link URL |
|---|---|
| Copernicus DEM GLO-30 (ESA), AWS Open Data | https://registry.opendata.aws/copernicus-dem/ |
| Copernicus Data Space Ecosystem (ESA) | https://dataspace.copernicus.eu/ |
| Artemis III region outlines (USGS data release) | https://doi.org/10.5066/P1MEQ6UK |
| LROC QuickMap (Arizona State University) | https://quickmap.lroc.asu.edu/ |
| JRC Global Surface Water (European Commission) | https://global-surface-water.appspot.com/ |
| Google Earth Engine | https://earthengine.google.com/ |
| EOxCloudless Sentinel-2 map (EOX, CC BY-NC-SA 4.0) | https://s2maps.eu/ |
| OpenStreetMap contributors | https://www.openstreetmap.org/copyright |
| Terrain Tiles (AWS Open Data; Mapzen, USGS SRTM, NOAA ETOPO1) | https://registry.opendata.aws/terrain-tiles/ |
| three.js | https://threejs.org/ |
| MapLibre GL JS | https://maplibre.org/ |
| GSAP | https://gsap.com/ |
| Lenis | https://github.com/darkroomengineering/lenis |
| Vite | https://vite.dev/ |
| Archivo typeface (SIL Open Font License) | https://fonts.google.com/specimen/Archivo |
| Loading animation by ZacharyCrespin (Uiverse.io, MIT) | https://uiverse.io/ |
| Impeccable design skill (Apache 2.0) | https://github.com/pbakaus/impeccable |
| scikit-learn | https://scikit-learn.org/ |
| rasterio | https://rasterio.readthedocs.io/ |
| Claude (Anthropic), AI coding and writing assistant | https://www.anthropic.com/claude |
| Google Gemini API ("Ask the analyst") | https://ai.google.dev/ |

Add the project repository, https://github.com/maroo2007/analog-finder, only
once it is public: right now it answers 404 to anyone outside the team, and
a link judges cannot open counts against us.

## Before clicking "Submit for Judging"

- [ ] Project name changed to Planetary Twin Finder.
- [ ] Demo link added, opened in a private browser window, under the
      30 second or 7 slide limit.
- [ ] https://duplicaa.vercel.app opened in a private window, Twin Finder
      and analyst working.
- [ ] GitHub repository public (or its link left out everywhere, including
      the website footer).
- [ ] China-affiliation question checked (`docs/JUDGING_CRITERIA.md`).
- [ ] Every team member on the Members tab, registered for the Cairo event.
- [ ] Both boxes ticked, Save Progress, then Submit for Judging, at least
      three hours before 11:59 p.m. Sunday.
