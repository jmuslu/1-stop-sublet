from __future__ import annotations

import json
from pathlib import Path

from scrapers.registry import load_sources
from scrapers.title_generator import generate_titles

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "src" / "data" / "generatedListings.json"


def main() -> None:
    listings = []
    seen_urls: set[str] = set()
    existing_by_platform = _existing_by_platform()

    for scraper in load_sources():
        scraped = [listing.to_json() for listing in scraper.scrape()]
        if not scraped and existing_by_platform.get(scraper.source.name):
            print(f"Warning: keeping existing {scraper.source.name} listings")
            scraped = existing_by_platform[scraper.source.name]
        for listing in scraped:
            if listing["sourceUrl"] in seen_urls:
                continue
            seen_urls.add(listing["sourceUrl"])
            listings.append(listing)

    if not listings and OUTPUT_PATH.exists():
        print(f"Warning: no listings scraped; keeping existing {OUTPUT_PATH}")
        return

    generate_titles(listings)
    listings.sort(key=lambda listing: listing["dateListed"], reverse=True)
    OUTPUT_PATH.write_text(json.dumps(listings, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(listings)} listings to {OUTPUT_PATH}")


def _existing_by_platform() -> dict[str, list[dict]]:
    if not OUTPUT_PATH.exists():
        return {}
    try:
        existing = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(existing, list):
        return {}

    by_platform: dict[str, list[dict]] = {}
    for listing in existing:
        if not isinstance(listing, dict):
            continue
        platform = listing.get("platform")
        if isinstance(platform, str):
            by_platform.setdefault(platform, []).append(listing)
    return by_platform


if __name__ == "__main__":
    main()
