import type { Listing } from '../types/listing';

/** Build the lowercased text blob a listing is searchable against. */
function haystack(listing: Listing): string {
  const bedrooms =
    listing.bedrooms === 0 ? 'studio' : `${listing.bedrooms} bed ${listing.bedrooms} br bedroom`;

  return [
    listing.title,
    listing.description,
    listing.location,
    listing.platform,
    listing.school,
    bedrooms,
    `${listing.bathrooms} bath ba`,
    listing.price != null ? `$${listing.price}` : 'ask price negotiable',
    listing.parking,
    ...(listing.amenities ?? []),
    ...(listing.extraCosts ?? []),
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase();
}

/**
 * Token-AND search: every whitespace-separated term in the query must appear
 * somewhere in the listing's searchable text. Case-insensitive. An empty query
 * matches everything. Lets renters search by amenity, location, size, etc.
 * (e.g. "mission hill laundry" or "2 bed allston").
 */
export function matchesSearch(listing: Listing, query: string): boolean {
  const terms = query.trim().toLowerCase().split(/\s+/).filter(Boolean);
  if (terms.length === 0) {
    return true;
  }
  const text = haystack(listing);
  return terms.every((term) => text.includes(term));
}
