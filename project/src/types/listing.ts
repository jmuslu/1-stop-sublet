export type ListingPlatform = string;

export interface Listing {
  id: string;
  title: string;
  titleGeneratedByAI?: boolean;
  description: string;
  price: number | null;
  location: string;
  bedrooms: number;
  bathrooms: number;
  platform: ListingPlatform;
  dateListed: string;
  imageUrl: string;
  sourceUrl: string;
  sourceVettedUsers?: boolean;
  sourceSubreddit?: string;
  sourceThreadTitle?: string;
  sourceAuthor?: string;
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
