import type { Listing } from '../types/listing';

export type LatLng = [number, number];

/**
 * The listing data has no real coordinates - only neighborhood strings (e.g.
 * "Mission Hill, Boston, MA"). We can't yet verify exact addresses, so the map
 * is an illustrative example: listings are grouped by neighborhood and shown as
 * a single pin at the neighborhood's approximate centroid. Nothing here claims
 * to be an exact location.
 */
const NEIGHBORHOOD_COORDS: Record<string, LatLng> = {
  'Mission Hill, MA': [42.3299, -71.1018],
  'Mission Hill, Boston, MA': [42.3299, -71.1018],
  'Allston, MA': [42.3537, -71.1322],
  'Allston, Boston, MA': [42.3537, -71.1322],
  'Fenway, MA': [42.3429, -71.0976],
  'Fenway, Boston, MA': [42.3429, -71.0976],
  'Back Bay, MA': [42.3503, -71.081],
  'Back Bay, Boston, MA': [42.3503, -71.081],
  'Roxbury Crossing, MA': [42.3314, -71.0956],
  'Roxbury Crossing, Boston, MA': [42.3314, -71.0956],
  'Ruggles, MA': [42.3362, -71.0892],
  'Ruggles, Boston, MA': [42.3362, -71.0892],
  'Cambridge, MA': [42.3736, -71.1097],
  'West Village, MA': [42.3376, -71.0915],
  'West Village, Boston, MA': [42.3376, -71.0915],
  'Roxbury, MA': [42.3247, -71.0951],
  'Roxbury, Boston, MA': [42.3247, -71.0951],
  'Downtown, MA': [42.3559, -71.0603],
  'Downtown, Boston, MA': [42.3559, -71.0603],
  'Jamaica Plain, MA': [42.3098, -71.1145],
  'Jamaica Plain, Boston, MA': [42.3098, -71.1145],
  'Symphony, MA': [42.3429, -71.0857],
  'Symphony, Boston, MA': [42.3429, -71.0857],
};

// Listings with no specific neighborhood ("Boston, MA" or anything unmapped)
// are collected into one "Boston area" pin placed centrally near campus.
const GENERIC_KEY = 'Boston area';
// Placed east of campus (toward the South End) so this large catch-all pin
// doesn't sit on top of the Northeastern campus marker.
const GENERIC_COORDS: LatLng = [42.345, -71.073];

/** Northeastern University campus - the anchor point of the map. */
export const NORTHEASTERN: { name: string; coords: LatLng } = {
  name: 'Northeastern University',
  coords: [42.3398, -71.0892],
};

/** Nearby MBTA stops, so renters can see each area relative to transit. */
export const TRANSIT_STOPS: { name: string; line: string; coords: LatLng }[] = [
  { name: 'Ruggles', line: 'Orange Line / Commuter Rail', coords: [42.3362, -71.0892] },
  { name: 'Northeastern University', line: 'Green Line E', coords: [42.3401, -71.0892] },
  { name: 'Symphony', line: 'Green Line E', coords: [42.3429, -71.0857] },
  { name: 'Massachusetts Ave', line: 'Orange Line', coords: [42.3415, -71.0838] },
  { name: 'Roxbury Crossing', line: 'Orange Line', coords: [42.3314, -71.0956] },
  { name: 'Back Bay', line: 'Orange Line / Commuter Rail', coords: [42.3475, -71.0757] },
];

export interface NeighborhoodGroup {
  key: string;
  label: string;
  coords: LatLng;
  listings: Listing[];
}

export function locationFilterValue(location: string): string {
  const normalized = location.trim().replace(/\s+/g, ' ');
  if (normalized === 'Boston, MA') {
    return normalized;
  }
  if (normalized.endsWith(', Boston, MA')) {
    return normalized.replace(', Boston, MA', ', MA');
  }
  return normalized;
}

/**
 * Group listings into neighborhood pins for the example map. Each known
 * neighborhood becomes one pin at its centroid; everything else collapses into
 * a single "Boston area" pin. Returns groups largest-first.
 */
export function groupByNeighborhood(listings: Listing[]): NeighborhoodGroup[] {
  const groups = new Map<string, NeighborhoodGroup>();

  for (const listing of listings) {
    const location = locationFilterValue(listing.location);
    const known = NEIGHBORHOOD_COORDS[location];
    const key = known ? location : GENERIC_KEY;
    const existing = groups.get(key);
    if (existing) {
      existing.listings.push(listing);
    } else {
      groups.set(key, {
        key,
        label: known ? location.split(',')[0].trim() : GENERIC_KEY,
        coords: known ?? GENERIC_COORDS,
        listings: [listing],
      });
    }
  }

  return Array.from(groups.values()).sort((a, b) => b.listings.length - a.listings.length);
}
