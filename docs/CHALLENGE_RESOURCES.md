# Challenge resources

The data and resources listed on the **Resources** tab of our challenge,
*Identify Earth Locations that Analog the Permanent Moon Base Locations and
Mars*, copied on 13 November 2026 from
https://www.spaceappschallenge.org/2026/challenges/permanent-moon-base-locations-and-mars/

Judges score relevance to the challenge, so name every source we use from this
list on the project page. The page's links carried a tracking parameter
(`?utm_source='chatgpt.com'`), which is removed below; the addresses are
otherwise unchanged.

NASA's note on the page: NASA does not endorse any non-U.S. Government entity
and is not responsible for information on non-U.S. Government websites. For
those websites, participants must follow that website's data use terms.

## NASA data and resources

### Earth

| Resource | What the page says |
|---|---|
| [NASA Earthdata Search](https://search.earthdata.nasa.gov/) | NASA's main portal for finding and downloading Earth science observations. |
| [NASA Worldview](https://worldview.earthdata.nasa.gov/) | Interactive viewer for exploring NASA satellite imagery and environmental observations. |

### Moon and Mars

| Resource | What the page says |
|---|---|
| [NASA Planetary Data System (PDS)](https://pds.nasa.gov/) | NASA's long-term archive for planetary data from orbiters, landers and rovers: lunar and Martian imagery, geoscience, atmospheres, plasma, cartography and more. |
| [NASA Lunar Reconnaissance Orbiter (LRO)](https://pds-geosciences.wustl.edu/missions/lro/) | LRO observations of the lunar surface from LROC, LOLA, Diviner, LEND, Mini-RF and other instruments. |
| [NASA LRO Diviner Lunar Data](https://pds-geosciences.wustl.edu/missions/lro/diviner.htm) | Lunar surface temperatures, especially useful for the poles. The page suggests comparing its polar and resource products with extreme cold, ice-bearing or other terrestrial environments. |

## Space agency partner resources

### CSA (Canadian Space Agency)

| Resource | What the page says |
|---|---|
| [RADARSAT Constellation Mission (RCM) data](https://donnees-data.asc-csa.gc.ca/en/dataset/rcm) | Three radar satellites that image Earth day or night in any weather, for maritime surveillance, disaster management and ecosystem monitoring. |
| [RADARSAT-1 data](https://donnees-data.asc-csa.gc.ca/en/dataset/radarsat1) | Synthetic aperture radar (SAR) archive from 1995 onward, imaging through cloud, smoke and haze. The whole archive is under an open licence. |
| [Synthetic Aperture Radar (SAR) Python tutorial](https://github.com/asc-csa/Synthetic_Aperture_Radar_Tutorial) | Working with SAR imagery in Python and QGIS: accessing and visualizing the data. |

### ESA (European Space Agency)

| Resource | What the page says |
|---|---|
| [Copernicus Data Space Ecosystem](https://dataspace.copernicus.eu/) | Free, open access to Sentinel Earth observation data (land, ocean, atmosphere) with visualization and processing tools. |
| [ESA Open Science Catalog](https://opensciencedata.esa.int/) | Catalogue of public geoscience datasets, products, experiments and workflows. |

### JAXA (Japan Aerospace Exploration Agency)

| Resource | What the page says |
|---|---|
| [JAXA G-Portal](https://gportal.jaxa.jp/gpr/index/index) | Earth observation products from JAXA missions, searchable by variable (precipitation, snow, vegetation and more). |

## Community

- [Space Apps Connect](https://github.com/nasa/spaceapps): the official
  discussion space on GitHub.

## How this list relates to what we already use

Facts from the code as of 13 November, to help decide what to add:

- **LOLA (on this list, under LRO).** We use LOLA already, but from NASA PGDA
  (`terrain.moon_patch`), not from the PDS Geosciences node linked here. Same
  instrument; credit both.
- **Diviner (on this list).** Used since 2026-11-14, as context on the Moon
  cards (not for matching): the south Polar Resource Product gives each
  Artemis region its temperatures and cold-trap and ice-stability shares.
  See `HANDOFF.md` section 4 and `src/run_diviner.py`.
- **Copernicus (on this list).** Our Earth elevation is the Copernicus DEM
  GLO-30, read from AWS Open Data. The ESA portal linked here is a different
  door to the Copernicus programme (mainly Sentinel imagery).
- **Earthdata Search and Worldview (on this list).** Our MODIS layers (NDVI,
  albedo) are NASA Earthdata products, read through Earth Engine. Worldview is
  a quick way to show judges imagery of a matched Earth site.
- **PDS (on this list).** MOLA and TES for Mars come from USGS Astropedia,
  which redistributes PDS data.
- **Not used:** the radar sources (RCM, RADARSAT-1, the SAR tutorial), the ESA
  Open Science Catalog and JAXA G-Portal.

This file covers the Resources tab only. The Details tab (the full challenge
statement) is not copied here yet.
