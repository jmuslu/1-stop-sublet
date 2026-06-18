import type { Listing } from '../types/listing';

interface ListingCardProps {
  listing: Listing;
}

function ListingCard({ listing }: ListingCardProps) {
  const imageCount = listing.imageUrls?.length ?? (listing.imageUrl ? 1 : 0);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const formatPrice = (price: number | null) => {
    if (price === null) {
      return 'Ask';
    }

    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
    }).format(price);
  };

  return (
    <a
      className="listing-card"
      href={listing.sourceUrl}
      target="_blank"
      rel="noreferrer"
      aria-label={`Open ${listing.title} on ${listing.platform}`}
    >
      <div className="listing-image-container">
        {listing.imageUrl ? (
          <>
            <img
              src={listing.imageUrl}
              alt={listing.title}
              className="listing-image"
              loading="lazy"
            />
            {imageCount > 1 && <span className="listing-photo-count">{imageCount} photos</span>}
          </>
        ) : (
          <div className="listing-no-photo">
            <span>No photos listed</span>
          </div>
        )}
        <span className="listing-platform-badge">{listing.platform}</span>
      </div>
      <div className="listing-content">
        <div className="listing-header">
          <h3 className="listing-title">{listing.title}</h3>
          <span className="listing-price">
            {formatPrice(listing.price)}
            {listing.price !== null && '/mo'}
          </span>
        </div>
        <p className="listing-location">{listing.location}</p>
        <p className="listing-description">{listing.description}</p>
        <div className="listing-meta">
          <span className="listing-detail">
            {listing.bedrooms === 0 ? 'Studio' : `${listing.bedrooms} BR`}
            {' / '}
            {listing.bathrooms} BA
          </span>
          <span className="listing-date">Listed {formatDate(listing.dateListed)}</span>
        </div>
        <div className="listing-signals">
          {listing.roommatesTotal !== undefined && (
            <span>{listing.roommatesTotal} total roommates</span>
          )}
          {listing.parking && <span>{listing.parking}</span>}
          {listing.sourceVettedUsers !== undefined && (
            <span>{listing.sourceVettedUsers ? 'Vetted source' : 'Unvetted source'}</span>
          )}
          {listing.sourceSubreddit && <span>{listing.sourceSubreddit}</span>}
          {listing.sourceThreadTitle && <span>{listing.sourceThreadTitle}</span>}
          {listing.sourceAuthor && <span>{listing.sourceAuthor}</span>}
        </div>
        {listing.amenities && listing.amenities.length > 0 && (
          <div className="listing-amenities">
            {listing.amenities.slice(0, 3).map((amenity) => (
              <span key={amenity}>{amenity}</span>
            ))}
          </div>
        )}
      </div>
    </a>
  );
}

export default ListingCard;
