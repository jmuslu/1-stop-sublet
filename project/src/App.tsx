import { useState, useMemo } from 'react';
import type { Listing, ListingPlatform, SortOption } from './types/listing';
import generatedListings from './data/generatedListings.json';
import Header from './components/Header';
import FilterBar from './components/FilterBar';
import ListingGrid from './components/ListingGrid';
import './App.css';

function App() {
  const [selectedPlatform, setSelectedPlatform] = useState<ListingPlatform | 'all'>('all');
  const [selectedLocation, setSelectedLocation] = useState('all');
  const [sortBy, setSortBy] = useState<SortOption>('date-desc');
  const listings = generatedListings as Listing[];

  const locations = useMemo(() => {
    const uniqueLocations = new Set(listings.map((l) => l.location));
    return Array.from(uniqueLocations).sort();
  }, [listings]);

  const platforms = useMemo(() => {
    const uniquePlatforms = new Set(listings.map((l) => l.platform));
    return Array.from(uniquePlatforms).sort();
  }, [listings]);

  const filteredAndSortedListings = useMemo(() => {
    let result = [...listings];

    if (selectedPlatform !== 'all') {
      result = result.filter((listing) => listing.platform === selectedPlatform);
    }

    if (selectedLocation !== 'all') {
      result = result.filter((listing) => listing.location === selectedLocation);
    }

    result.sort((a, b) => {
      switch (sortBy) {
        case 'date-desc':
          return new Date(b.dateListed).getTime() - new Date(a.dateListed).getTime();
        case 'date-asc':
          return new Date(a.dateListed).getTime() - new Date(b.dateListed).getTime();
        case 'price-desc':
          return (b.price ?? -1) - (a.price ?? -1);
        case 'price-asc':
          return (a.price ?? Number.MAX_SAFE_INTEGER) - (b.price ?? Number.MAX_SAFE_INTEGER);
        default:
          return 0;
      }
    });

    return result;
  }, [listings, selectedPlatform, selectedLocation, sortBy]);

  return (
    <div className="app">
      <Header />
      <main className="main-content">
        <FilterBar
          selectedPlatform={selectedPlatform}
          onPlatformChange={setSelectedPlatform}
          platforms={platforms}
          selectedLocation={selectedLocation}
          onLocationChange={setSelectedLocation}
          locations={locations}
          sortBy={sortBy}
          onSortChange={setSortBy}
        />
        <div className="results-count">
          {filteredAndSortedListings.length} listings found
        </div>
        <ListingGrid listings={filteredAndSortedListings} />
      </main>
      <footer className="footer">
        <p>1StopSublet - Your centralized sublet marketplace</p>
      </footer>
    </div>
  );
}

export default App;
