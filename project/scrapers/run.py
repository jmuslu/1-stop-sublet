from __future__ import annotations

import json
from pathlib import Path

from scrapers.registry import load_sources

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "src" / "data" / "generatedListings.json"


def main() -> None:
    listings = []
    seen_urls: set[str] = set()

    for scraper in load_sources():
        for listing in scraper.scrape():
            if listing.sourceUrl in seen_urls:
                continue
            seen_urls.add(listing.sourceUrl)
            listings.append(listing.to_json())

    if not listings and OUTPUT_PATH.exists():
        print(f"Warning: no listings scraped; keeping existing {OUTPUT_PATH}")
        return

    listings.sort(key=lambda listing: listing["dateListed"], reverse=True)
    OUTPUT_PATH.write_text(json.dumps(listings, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(listings)} listings to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
