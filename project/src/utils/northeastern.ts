import type { Listing } from '../types/listing';

// Signals that a listing is from / for the Northeastern community.
const NEU_RE = /northeastern|huskies|husky|\bneu\b/i;
// Neighborhoods on or next to NU's campus — relevant even when the poster is elsewhere.
const NEAR_NEU_RE =
  /mission hill|ruggles|roxbury crossing|\broxbury\b|fenway|symphony|huntington|columbus ave/i;
// Other Boston-area schools we want ranked below Northeastern content.
const OTHER_SCHOOL_RE =
  /\btufts\b|\bharvard\b|\bmit\b|boston university|\bbu\b|berklee|emerson|suffolk|simmons|wentworth|boston college|\bbc\b|umass|mass ?art|new england conservatory|\bnec\b/i;

function searchableText(listing: Listing): string {
  return [
    listing.title,
    listing.description,
    listing.location,
    listing.school,
    listing.sourceSubreddit,
    listing.sourceThreadTitle,
    ...(listing.amenities ?? []),
  ]
    .filter(Boolean)
    .join(' ');
}

/** True when the listing is explicitly tied to Northeastern. */
export function isNortheastern(listing: Listing): boolean {
  return NEU_RE.test(searchableText(listing));
}

/**
 * Relevance score for ordering the feed: Northeastern listings/asks float to the
 * top, near-campus listings sit in the middle, and listings tied to other Boston
 * schools sink to the bottom. Higher is more relevant.
 */
export function northeasternScore(listing: Listing): number {
  const text = searchableText(listing);
  let score = 0;
  if (NEU_RE.test(text)) score += 100;
  if (NEAR_NEU_RE.test(text)) score += 40;
  if (OTHER_SCHOOL_RE.test(text) && !NEU_RE.test(text)) score -= 60;
  return score;
}
