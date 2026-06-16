import type { Listing } from '../types/listing';
import ListingCard from './ListingCard';

interface ListingGridProps {
  listings: Listing[];
}

function ListingGrid({ listings }: ListingGridProps) {
  if (listings.length === 0) {
    return (
      <div className="no-listings">
        <p>No listings match your filters</p>
      </div>
    );
  }

  return (
    <div className="listing-grid">
      {listings.map((listing) => (
        <ListingCard key={listing.id} listing={listing} />
      ))}
    </div>
  );
}

export default ListingGrid;
