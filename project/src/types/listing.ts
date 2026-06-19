export type ListingPlatform = string;

export interface Listing {
  id: string;
  title: string;
  description: string;
  price: number | null;
  location: string;
  bedrooms: number;
  bathrooms: number;
  platform: ListingPlatform;
  dateListed: string;
  imageUrl: string | null;
  sourceUrl: string;
  sourceVettedUsers?: boolean;
  sourceSubreddit?: string | null;
  sourceThreadTitle?: string | null;
  sourceAuthor?: string | null;
  sourceIntent?: string | null;
  school?: string | null;
  imageUrls?: string[];
  availabilityLabel?: string | null;
  availableFrom?: string | null;
  availableTo?: string | null;
  termTags?: string[];
  amenities?: string[];
  roommatesTotal?: number;
  floor?: string;
  parking?: string;
  extraCosts?: string[];
  utilitiesNotes?: string;
  applianceNotes?: string;
  contactEmail?: string;
  contactPhone?: string;
}

export type SortOption = 'date-desc' | 'date-asc' | 'price-desc' | 'price-asc';
