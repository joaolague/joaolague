// Geographic reference for the Torres (RS) domain.
//
// Three coordinate systems are used:
//   lat/lon  - WGS84 degrees
//   EN       - local east/north in metres around ORIGIN (equirectangular, fine for ~10 km)
//   coast    - x = seaward (shore-normal), y = alongshore (towards NNE), metres
// Three.js world: X = east, Y = up, Z = -north.

export const ORIGIN = { lat: -29.347, lon: -49.727 }; // Praia Grande shoreline (approx.)

// Mean coastline bearing (from north, clockwise). The RS/SC coast near Torres runs ~N30E.
export const COAST_BEARING = 32;
const SEAWARD_BEARING = COAST_BEARING + 90;

const DEG = Math.PI / 180;
const M_PER_DEG_LAT = 110850;
const M_PER_DEG_LON = 111320 * Math.cos(ORIGIN.lat * DEG);

// Unit vectors (east, north) of the coast frame axes
export const NHAT = [Math.sin(SEAWARD_BEARING * DEG), Math.cos(SEAWARD_BEARING * DEG)];
export const THAT = [Math.sin(COAST_BEARING * DEG), Math.cos(COAST_BEARING * DEG)];

// Domain extent in the coast frame (metres)
export const DOMAIN = { x0: -1500, x1: 3500, y0: -3200, y1: 4000 };

export function lonLatToEN(lon, lat) {
  return [(lon - ORIGIN.lon) * M_PER_DEG_LON, (lat - ORIGIN.lat) * M_PER_DEG_LAT];
}

export function enToLonLat(e, n) {
  return [ORIGIN.lon + e / M_PER_DEG_LON, ORIGIN.lat + n / M_PER_DEG_LAT];
}

export function enToCoast(e, n) {
  return [e * NHAT[0] + n * NHAT[1], e * THAT[0] + n * THAT[1]];
}

export function coastToEN(x, y) {
  return [x * NHAT[0] + y * THAT[0], x * NHAT[1] + y * THAT[1]];
}

export function coastToLonLat(x, y) {
  const [e, n] = coastToEN(x, y);
  return enToLonLat(e, n);
}

export function lonLatToCoast(lon, lat) {
  const [e, n] = lonLatToEN(lon, lat);
  return enToCoast(e, n);
}

// Bearing (deg, "towards") to a unit vector in the coast frame
export function bearingToCoastVec(bearingTo) {
  const e = Math.sin(bearingTo * DEG);
  const n = Math.cos(bearingTo * DEG);
  return enToCoast(e, n);
}

// Landmarks. Positions are approximate and should be checked against a survey/orthophoto.
// kind: 'headland' feeds the procedural terrain; 'beach' is label only.
export const LANDMARKS = [
  { name: 'Barra do Mampituba (Molhes)', lat: -29.3225, lon: -49.7095, kind: 'river' },
  { name: 'Praia dos Molhes', lat: -29.3285, lon: -49.7140, kind: 'beach' },
  { name: 'Morro do Farol', lat: -29.3350, lon: -49.7195, kind: 'headland', height: 48, protrusion: 170, width: 150 },
  { name: 'Praia da Cal', lat: -29.3383, lon: -49.7212, kind: 'beach' },
  { name: 'Morro das Furnas', lat: -29.3410, lon: -49.7232, kind: 'headland', height: 38, protrusion: 120, width: 110 },
  { name: 'Praia Grande', lat: -29.3470, lon: -49.7270, kind: 'beach' },
  { name: 'Guarita (Torre Sul)', lat: -29.3535, lon: -49.7315, kind: 'headland', height: 45, protrusion: 190, width: 170 },
  { name: 'Praia da Guarita', lat: -29.3575, lon: -49.7345, kind: 'beach' },
  { name: 'Praia de Itapeva', lat: -29.3700, lon: -49.7440, kind: 'beach' },
  { name: 'Ilha dos Lobos', lat: -29.3445, lon: -49.7010, kind: 'island' },
];

// Camera presets: target and camera position in coast frame (x, y, height)
export const CAMERA_PRESETS = {
  'Vista geral': { target: [600, 400, 0], eye: [4200, -2600, 1900] },
  'Praia Grande': { target: [120, -150, 0], eye: [900, -900, 160] },
  'Guarita': { target: [100, -850, 0], eye: [700, -1500, 140] },
  'Molhes': { target: [150, 3150, 0], eye: [900, 2500, 170] },
  'Ilha dos Lobos': { target: [1950, 1550, 0], eye: [2700, 900, 250] },
};
