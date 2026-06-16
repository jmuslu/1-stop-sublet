from __future__ import annotations

from scrapers.base import ListingScraper, NormalizedListing


class SeedListingScraper(ListingScraper):
    """Loads configured seed listings while live sources are being connected."""

    def scrape(self) -> list[NormalizedListing]:
        listings = self.source.config.get("listings", [])
        return [
            NormalizedListing(
                id=raw["id"],
                title=raw["title"],
                description=raw["description"],
                price=int(raw["price"]),
                location=raw["location"],
                bedrooms=int(raw["bedrooms"]),
                bathrooms=float(raw["bathrooms"]),
                platform=self.source.name,
                dateListed=raw["dateListed"],
                imageUrl=raw["imageUrl"],
                sourceUrl=raw["sourceUrl"],
                sourceVettedUsers=self.source.vetted_users,
                amenities=raw.get("amenities", []),
                roommatesTotal=raw.get("roommatesTotal"),
                floor=raw.get("floor"),
                parking=raw.get("parking"),
                extraCosts=raw.get("extraCosts", []),
                utilitiesNotes=raw.get("utilitiesNotes"),
                applianceNotes=raw.get("applianceNotes"),
            )
            for raw in listings
        ]
