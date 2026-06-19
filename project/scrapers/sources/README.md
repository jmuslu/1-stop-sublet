# Scraper Sources

Each source gets one config file here and, when needed, one Python scraper class.

The scraper output is static: `npm run scrape` writes `src/data/generatedListings.json`, and the Vite app imports that file at build time. This keeps 1StopSublet deployable on GitHub Pages without a backend.

To add a real source:

1. Create a scraper class in this folder that extends `ListingScraper`.
2. Add that class to `SCRAPER_TYPES` in `../registry.py`.
3. Add a JSON config in this folder with its source-specific knobs.
4. Normalize every item to `NormalizedListing`, especially `sourceUrl`, `dateListed`, `price`, `location`, `amenities`, and `sourceVettedUsers`.

Use one source per file. That keeps website-specific parsing, rate limits, selectors, and cleanup rules easy to swap without touching the React app.

## Current Sources

- `reddit_neu_housing.json` uses Reddit's public Atom feed for the r/NEU housing megathread. The JSON API is often blocked for unauthenticated requests, so the scraper intentionally uses RSS/Atom and keeps previous generated data for that source if Reddit rate-limits a scheduled build. Listers are unverified (`vetted_users: false`).
- `facebook_neu_group.json` first attempts to read the public mobile Facebook group preview without an account. If Facebook returns a login page or too few public posts, `scrapers/manual/facebook_export_browser_console.js` can still be run in a logged-in browser to download visible posts as `facebook_group_posts.json`, then the scraper normalizes those posts into the same listing contract.
- `neu_aptsearch.json` reads Northeastern's official off-campus housing portal through its public listing search endpoint, using `curl_cffi` to make a Chrome-like request because plain HTTP clients receive 403s. It is the university's own channel, so it surfaces as an official portal (`vetted_users: false`) rather than peer-verified.
- `sblt.json` reads SBLT's (https://www.sblt.app) Supabase `listings` table through its public PostgREST endpoint. The `anon_key` is the public client key shipped in SBLT's web bundle and is meant to be public. SBLT's `.edu` gate only applies to posting or contacting a lister, so every lister is a verified student (`vetted_users: true`).
- `subletr.json` parses Subletr's (https://www.subletr.com) server-rendered `/listings` index; no API key or sign-in is needed to browse. Posting requires a verified student account, so `vetted_users: true`.
