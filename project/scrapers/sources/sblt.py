from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any

from scrapers.base import ListingScraper, NormalizedListing


class SbltScraper(ListingScraper):
    """SBLT (https://www.sblt.app) — a verified-student sublet platform.

    SBLT is a single-page app backed by Supabase. Its ``listings`` table allows
    anonymous SELECT (so visitors can browse before signing in), so we read
    listings straight from the public PostgREST endpoint. The ``anon_key`` in the
    config is the public client key shipped in SBLT's web bundle — it is meant to
    be public and is safe to commit. The ``.edu`` sign-in gate only applies to
    posting a listing or contacting a lister, which is why ``vetted_users`` is
    true: every lister is a verified student.

    Follows the same contract/fallback pattern as the Reddit scraper: any network
    or parsing failure prints a warning and returns ``[]`` so the build stays green
    and the previously generated data is kept.
    """

    def scrape(self) -> list[NormalizedListing]:
        cfg = self.source.config
        base = cfg["supabase_url"].rstrip("/")
        table = cfg.get("table", "listings")
        anon = cfg["anon_key"]
        max_items = int(cfg.get("max_items", 100))

        query = (
            f"{base}/rest/v1/{table}"
            f"?select=*&status=eq.active&order=created_at.desc&limit={max_items}"
        )

        try:
            rows = self._fetch_json(query, anon)
        except (urllib.error.URLError, json.JSONDecodeError, ValueError) as exc:
            print(f"Warning: could not fetch {self.source.name}: {exc}")
            return []

        listings: list[NormalizedListing] = []
        for row in rows:
            listing = self._normalize(row)
            if listing is not None:
                listings.append(listing)
        return listings

    def _fetch_json(self, url: str, anon: str) -> list[dict[str, Any]]:
        request = urllib.request.Request(
            url,
            headers={
                "apikey": anon,
                "Authorization": f"Bearer {anon}",
                "Accept": "application/json",
                "User-Agent": self.source.config.get(
                    "user_agent",
                    "Mozilla/5.0 1StopSublet/0.1 (housing aggregation)",
                ),
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
        if not isinstance(data, list):
            raise ValueError("Supabase response was not a list of rows")
        return data

    def _normalize(self, row: dict[str, Any]) -> NormalizedListing | None:
        listing_id = row.get("id")
        if not listing_id:
            return None

        description = re.sub(r"\s+", " ", str(row.get("description") or "")).strip()
        title = str(row.get("title") or "").strip() or "SBLT student sublet"
        site = self.source.config.get("site_url", "https://www.sblt.app").rstrip("/")

        return NormalizedListing(
            id=f"sblt-{listing_id}",
            title=self._trim(title, 80),
            description=self._trim(description, 280),
            price=self._to_int(row.get("price")),
            location=self._location(row),
            bedrooms=self._bedrooms(row.get("bedrooms")),
            bathrooms=self._bathrooms(description),
            platform=self.source.name,
            dateListed=str(row.get("created_at") or "")[:10] or "1970-01-01",
            imageUrl=self._image(row),
            sourceUrl=f"{site}/?listing={listing_id}",
            sourceVettedUsers=self.source.vetted_users,
            school=self._school(row),
            amenities=self._amenities(row),
            roommatesTotal=self._roommates(row.get("roommates")),
            applianceNotes=self._availability(row),
        )

    def _school(self, row: dict[str, Any]) -> str | None:
        school = str(row.get("school") or "").strip()
        # SBLT seeds some rows with a bare "University" placeholder; treat as unknown.
        if not school or school.lower() == "university":
            return None
        return school

    def _to_int(self, value: Any) -> int | None:
        try:
            if value is None:
                return None
            return int(float(value))
        except (TypeError, ValueError):
            return None

    def _location(self, row: dict[str, Any]) -> str:
        neighborhood = str(row.get("location") or "").strip()
        default = self.source.config.get("default_location", "Boston, MA")
        if neighborhood:
            return f"{neighborhood}, Boston, MA"
        return default

    def _bedrooms(self, value: Any) -> int:
        text = str(value or "")
        if re.search(r"studio", text, re.IGNORECASE):
            return 0
        match = re.search(r"(\d+)", text)
        return int(match.group(1)) if match else 1

    def _bathrooms(self, description: str) -> float:
        match = re.search(r"(\d+(?:\.5)?)\s*(?:bath|baths|bathroom|bathrooms|ba)\b", description, re.IGNORECASE)
        return float(match.group(1)) if match else 1.0

    def _image(self, row: dict[str, Any]) -> str:
        if row.get("image_url"):
            return str(row["image_url"])
        photos = row.get("photos")
        if isinstance(photos, list) and photos:
            return str(photos[0])
        return self.source.config.get("default_image_url", "")

    def _amenities(self, row: dict[str, Any]) -> list[str]:
        amenities = [str(a) for a in (row.get("amenities") or []) if isinstance(a, str)]
        return amenities[:8]

    def _roommates(self, value: Any) -> int | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return int(value)
        return None

    def _availability(self, row: dict[str, Any]) -> str | None:
        start = str(row.get("available_from") or "").strip()
        end = str(row.get("available_to") or "").strip()
        if start and end:
            return f"Available {start} to {end}"
        if start:
            return f"Available from {start}"
        return None

    def _trim(self, value: str, limit: int) -> str:
        normalized = re.sub(r"\s+", " ", value).strip()
        if len(normalized) <= limit:
            return normalized
        return normalized[: limit - 1].rstrip() + "…"
