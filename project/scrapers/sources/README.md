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

- `reddit_neu_housing.json` uses Reddit's public Atom feed for the r/NEU housing megathread. The JSON API is often blocked for unauthenticated requests, so the scraper intentionally uses RSS/Atom and keeps the previous generated data if Reddit rate-limits a scheduled build. Listers are unverified (`vetted_users: false`).
- `sblt.json` reads SBLT's (https://www.sblt.app) Supabase `listings` table through its public PostgREST endpoint. The `anon_key` is the public client key shipped in SBLT's web bundle and is meant to be public. SBLT's `.edu` gate only applies to posting or contacting a lister, so every lister is a verified student (`vetted_users: true`).
- `subletr.json` parses Subletr's (https://www.subletr.com) server-rendered `/listings` index — no API key or sign-in needed to browse. Posting requires a verified student account, so `vetted_users: true`.

## Potential Sources

These are scaffolded but not live. The scraper and config exist and are registered, but ship disabled until a blocker is resolved.

- `neu_aptsearch.json` targets Northeastern's official off-campus portal (https://aptsearch.northeastern.edu), filtered to Sublets Only. It is the university's own channel, so it would surface as an "official portal" (`vetted_users: false`) rather than peer-verified. **Disabled (`enabled: false`):** the portal sits behind Akamai bot protection and returns HTTP 403 to non-browser clients. The scraper is wired and ready — enable it once requests can be served through an approved browser/proxy path, and validate the parser against the real markup at that point.
