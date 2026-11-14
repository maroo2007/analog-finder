// Coordinates shared by every globe on the site. The vector convention
// matches three.js sphere UVs, so an equirectangular texture lines up.
import * as THREE from 'three';

export const DEG = Math.PI / 180;

/** Latitude/longitude (degrees) to a point on a sphere of radius r. */
export function latLonToVec(lat, lon, r = 1) {
  const la = lat * DEG; const lo = lon * DEG;
  return new THREE.Vector3(r * Math.cos(la) * Math.cos(lo), r * Math.sin(la), -r * Math.cos(la) * Math.sin(lo));
}

/** A point on the unit sphere (in the globe's own frame) back to lat/lon. */
export function vecToLatLon(v) {
  const n = v.clone().normalize();
  return { lat: Math.asin(n.y) / DEG, lon: Math.atan2(-n.z, n.x) / DEG };
}

/** Y rotation that turns longitude `lon` to face the camera (+z). */
export const faceLon = (lon) => -Math.PI / 2 - lon * DEG;

/** Great-circle angle between two points, in degrees. */
export function angleDeg(a, b) {
  const p1 = a.lat * DEG; const p2 = b.lat * DEG;
  const dp = p2 - p1; const dl = (b.lon - a.lon) * DEG;
  const h = Math.sin(dp / 2) ** 2 + Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) ** 2;
  return (2 * Math.asin(Math.min(1, Math.sqrt(h)))) / DEG;
}

/** Distance on Earth in kilometres. */
export const earthKm = (a, b) => angleDeg(a, b) * DEG * 6371;
