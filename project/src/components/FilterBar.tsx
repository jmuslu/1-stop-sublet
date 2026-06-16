import type { ListingPlatform, SortOption } from '../types/listing';

interface FilterBarProps {
  selectedPlatform: ListingPlatform | 'all';
  onPlatformChange: (platform: ListingPlatform | 'all') => void;
  platforms: ListingPlatform[];
  selectedLocation: string;
  onLocationChange: (location: string) => void;
  locations: string[];
  sortBy: SortOption;
  onSortChange: (sort: SortOption) => void;
}

function FilterBar({
  selectedPlatform,
  onPlatformChange,
  platforms,
  selectedLocation,
  onLocationChange,
  locations,
  sortBy,
  onSortChange,
}: FilterBarProps) {
  const platformOptions: (ListingPlatform | 'all')[] = ['all', ...platforms];

  return (
    <div className="filter-bar">
      <div className="filter-group">
        <label htmlFor="platform-filter">Platform</label>
        <select
          id="platform-filter"
          value={selectedPlatform}
          onChange={(e) => onPlatformChange(e.target.value as ListingPlatform | 'all')}
        >
          {platformOptions.map((platform) => (
            <option key={platform} value={platform}>
              {platform === 'all' ? 'All Platforms' : platform}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label htmlFor="location-filter">Location</label>
        <select
          id="location-filter"
          value={selectedLocation}
          onChange={(e) => onLocationChange(e.target.value)}
        >
          <option value="all">All Locations</option>
          {locations.map((location) => (
            <option key={location} value={location}>
              {location}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label htmlFor="sort-filter">Sort By</label>
        <select
          id="sort-filter"
          value={sortBy}
          onChange={(e) => onSortChange(e.target.value as SortOption)}
        >
          <option value="date-desc">Newest First</option>
          <option value="date-asc">Oldest First</option>
          <option value="price-asc">Price: Low to High</option>
          <option value="price-desc">Price: High to Low</option>
        </select>
      </div>
    </div>
  );
}

export default FilterBar;
