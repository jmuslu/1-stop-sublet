# Scraper Sources

Each source gets one config file here and, when needed, one Python scraper class.

The scraper output is static: `npm run scrape` writes `src/data/generatedListings.json`, and the Vite app imports that file at build time. This keeps 1StopSublet deployable on GitHub Pages without a backend.

To add a real source:

1. Create a scraper class in this folder that extends `ListingScraper`.
2. Add that class to `SCRAPER_TYPES` in `../registry.py`.
3. Add a JSON config in this folder with its source-specific knobs.
4. Normalize every item to `NormalizedListing`, especially `sourceUrl`, `dateListed`, `price`, `location`, `amenities`, and `sourceVettedUsers`.

Use one source per file. That keeps website-specific parsing, rate limits, selectors, and cleanup rules easy to swap without touching the React app.
