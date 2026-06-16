export type ListingPlatform = string;

export interface Listing {
  id: string;
  title: string;
  description: string;
  price: number;
  location: string;
  bedrooms: number;
  bathrooms: number;
  platform: ListingPlatform;
  dateListed: string;
  imageUrl: string;
  sourceUrl: string;
  sourceVettedUsers?: boolean;
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
