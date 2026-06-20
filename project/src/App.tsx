import { useState, useMemo, useEffect } from 'react';
import type { Listing, ListingPlatform, SortOption } from './types/listing';
import generatedListings from './data/generatedListings.json';
import Header, { type View } from './components/Header';
import Home from './components/Home';
import FilterBar from './components/FilterBar';
import ListingGrid from './components/ListingGrid';
import { useTheme } from './hooks/useTheme';
import { northeasternScore } from './utils/northeastern';
import './App.css';

function App() {
  const [view, setView] = useState<View>('home');
  const { theme, toggleTheme } = useTheme();
  const [selectedPlatform, setSelectedPlatform] = useState<ListingPlatform | 'all'>('all');
  const [selectedLocation, setSelectedLocation] = useState('all');
  const [sortBy, setSortBy] = useState<SortOption>('date-desc');
  const listings = generatedListings as Listing[];

  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [view]);

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
      // Northeastern listings/asks rank first, other Boston schools last; the
      // chosen sort then orders listings within each relevance tier.
      const relevance = northeasternScore(b) - northeasternScore(a);
      if (relevance !== 0) {
        return relevance;
      }

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
      <Header
        view={view}
        onNavigate={setView}
        theme={theme}
        onToggleTheme={toggleTheme}
      />
      {view === 'home' ? (
        <Home listings={listings} onBrowse={() => setView('browse')} />
      ) : (
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
          {selectedPlatform === 'Facebook' && (
            <p className="source-note">
              Facebook only shows a limited public preview here. Sign in to Facebook to view more posts from the group.
            </p>
          )}
          <div className="results-count">
            {filteredAndSortedListings.length} listings found
          </div>
          <ListingGrid listings={filteredAndSortedListings} />
        </main>
      )}
      <footer className="footer">
        <p>1StopSublet — your centralized sublet marketplace for the Northeastern community</p>
      </footer>
    </div>
  );
}

export default App;
