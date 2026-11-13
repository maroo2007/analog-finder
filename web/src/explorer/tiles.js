// Map layers for the Earth view, built into ONE MapLibre style so that
// switching layers only shows and hides them: nothing reloads, the camera
// and pins stay. Terms and attribution checked 2026-11-13.
//
// Satellite is three stacked sources, fastest first, so the view is never
// black and sharpens as better tiles arrive:
// 1. NASA GIBS Blue Marble (to zoom 8): about 0.4 s a tile.
// 2. NASA GIBS Landsat WELD global annual composite, 30 m (to zoom 12):
//    about 0.7 to 1.2 s a tile.
// 3. EOX Sentinel-2 cloudless 2025 (to zoom 14): the sharpest, but EOX's
//    free server took 2 to 25 s a tile in testing (it has no speed
//    guarantee), so it fills in last.
// GIBS acknowledgement text: https://www.earthdata.nasa.gov/engage/open-data-services-software/earthdata-developer-portal/gibs-api
// EOX licence (2025 layer CC BY-NC-SA 4.0, non-commercial use unrestricted
// with attribution): https://cloudless.eox.at/documentation/license
// OpenStreetMap standard tiles (see the Map notes below).
// Terrain Tiles on AWS: https://registry.opendata.aws/terrain-tiles/ and
// https://github.com/tilezen/joerd/blob/master/docs/attribution.md
// Esri World Imagery needs an ArcGIS key under Esri's current terms, so it
// is used only when VITE_ESRI_API_KEY is set; then it replaces the slow
// EOX layer as the sharp top layer (fast and sharp from the first second).

const S2_YEAR = 2025;
const GIBS = 'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best';
const GIBS_ATTRIBUTION = 'We acknowledge the use of imagery provided by services from NASA\'s Global Imagery Browse Services (<a href="https://www.earthdata.nasa.gov/engage/open-data-services-software/earthdata-developer-portal/gibs-api" target="_blank" rel="noopener">GIBS</a>), part of NASA\'s Earth Science Data and Information System (ESDIS)';
const S2_ATTRIBUTION = `<a href="https://cloudless.eox.at" target="_blank" rel="noopener">EOxCloudless</a> by EOX IT Services GmbH (Contains modified Copernicus Sentinel data ${S2_YEAR})`;
const ESRI_ATTRIBUTION = 'Source: Esri, Vantor, Earthstar Geographics, and the GIS User Community';
const TERRAIN_ATTRIBUTION = '<a href="https://registry.opendata.aws/terrain-tiles/" target="_blank" rel="noopener">Terrain Tiles</a>: Mapzen; SRTM courtesy of the U.S. Geological Survey; ETOPO1 by U.S. NOAA; and <a href="https://github.com/tilezen/joerd/blob/master/docs/attribution.md" target="_blank" rel="noopener">others</a>';

// Map: OpenStreetMap's standard raster map. OpenFreeMap's vector tiles were
// tried first but weigh up to 1.5 MB at low zoom and took 2 to 20 s, leaving
// the globe white. OSM tiles are 2 to 22 KB and arrived in under a second.
// Tile policy (interactive use allowed; attribution must be clearly on the
// map; no prefetching; keep the browser's Referer):
// https://operations.osmfoundation.org/policies/tiles/
const OSM_ATTRIBUTION = '© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors';
// Terrain: NASA GIBS ASTER GDEM greyscale shaded relief as the fast base
// (to zoom 12, about 0.5 to 1 s a tile), AWS Terrain Tiles hillshade on top
// for close-up detail (those took 1 to 15 s in testing, so they come second).
const ASTER_ATTRIBUTION = 'ASTER GDEM is a product of METI and NASA';
const esriKey = import.meta.env.VITE_ESRI_API_KEY;

/** Sources and layers for satellite and terrain (map comes from OpenFreeMap). */
export function baseSources() {
  const sharp = esriKey
    ? {
      type: 'raster',
      tiles: [`https://ibasemaps-api.arcgis.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}?token=${encodeURIComponent(esriKey)}`],
      tileSize: 256, maxzoom: 19, attribution: ESRI_ATTRIBUTION,
    }
    : {
      type: 'raster',
      tiles: [`https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-${S2_YEAR}_3857/default/g/{z}/{y}/{x}.jpg`],
      tileSize: 256, maxzoom: 14, attribution: S2_ATTRIBUTION,
    };
  return {
    'sat-bluemarble': {
      type: 'raster',
      tiles: [`${GIBS}/BlueMarble_ShadedRelief_Bathymetry/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpeg`],
      tileSize: 256, maxzoom: 8, attribution: GIBS_ATTRIBUTION,
    },
    'sat-landsat': {
      type: 'raster',
      tiles: [`${GIBS}/Landsat_WELD_CorrectedReflectance_TrueColor_Global_Annual/default/default/GoogleMapsCompatible_Level12/{z}/{y}/{x}.jpeg`],
      tileSize: 256, minzoom: 6, maxzoom: 12,
    },
    'sat-sharp': sharp,
    'map-osm': {
      type: 'raster',
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256, maxzoom: 19, attribution: OSM_ATTRIBUTION,
    },
    'terrain-aster': {
      type: 'raster',
      tiles: [`${GIBS}/ASTER_GDEM_Greyscale_Shaded_Relief/default/GoogleMapsCompatible_Level12/{z}/{y}/{x}.jpg`],
      tileSize: 256, maxzoom: 12, attribution: `${GIBS_ATTRIBUTION}; ${ASTER_ATTRIBUTION}`,
    },
    dem: {
      type: 'raster-dem',
      tiles: ['https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'],
      encoding: 'terrarium', tileSize: 256, maxzoom: 14, attribution: TERRAIN_ATTRIBUTION,
    },
  };
}

export const GROUND = '#06080b';

/** Layer groups: which style layers each switch position shows. */
export function baseLayers() {
  return {
    satellite: [
      { id: 'sat-bluemarble', type: 'raster', source: 'sat-bluemarble', paint: { 'raster-fade-duration': 0 } },
      // Landsat is a little pale; lift it towards the Sentinel-2 look.
      { id: 'sat-landsat', type: 'raster', source: 'sat-landsat', minzoom: 6, paint: { 'raster-fade-duration': 250, 'raster-contrast': 0.25, 'raster-saturation': 0.15 } },
      { id: 'sat-sharp', type: 'raster', source: 'sat-sharp', minzoom: 5, paint: { 'raster-fade-duration': 400 } },
    ],
    map: [
      { id: 'map-osm', type: 'raster', source: 'map-osm', paint: { 'raster-fade-duration': 150 } },
    ],
    terrain: [
      { id: 'terrain-ground', type: 'background', paint: { 'background-color': '#1a1f26' } },
      // The fast base: shaded relief, toned down slightly for the dark page.
      { id: 'terrain-aster', type: 'raster', source: 'terrain-aster', paint: { 'raster-fade-duration': 150, 'raster-brightness-max': 0.9, 'raster-contrast': 0.15 } },
      // Sharper shading drawn over it when zoomed in, once those tiles land.
      {
        id: 'terrain-relief', type: 'hillshade', source: 'dem', minzoom: 9,
        paint: {
          'hillshade-exaggeration': 0.45,
          'hillshade-illumination-direction': 315,
          'hillshade-shadow-color': 'rgba(6, 8, 11, 0.55)',
          'hillshade-highlight-color': 'rgba(243, 245, 247, 0.35)',
          'hillshade-accent-color': 'rgba(58, 64, 72, 0.4)',
        },
      },
    ],
  };
}
