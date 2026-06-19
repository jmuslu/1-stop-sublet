from __future__ import annotations

import re
from typing import Any

from scrapers.base import ListingScraper, NormalizedListing


class NeuAptSearchScraper(ListingScraper):
    """Northeastern's official off-campus housing portal.

    The public page is protected from plain HTTP clients, but its own public BFF
    search endpoint can be read with a normal Chrome-like request. The API key
    used here is exposed in the site's browser bundle and is not a private user
    credential.
    """

    def scrape(self) -> list[NormalizedListing]:
        max_items = int(self.source.config.get("max_items", 100))
        try:
            placards = self._fetch_placards()
        except Exception as exc:
            print(f"Warning: could not fetch {self.source.name}: {exc}")
            return []

        listings: list[NormalizedListing] = []
        for placard in placards:
            listing = self._normalize(placard)
            if listing is not None:
                listings.append(listing)
            if len(listings) >= max_items:
                break
        return listings

    def _fetch_placards(self) -> list[dict[str, Any]]:
        try:
            from curl_cffi import requests
        except ImportError as exc:
            raise RuntimeError("curl_cffi is not installed") from exc

        response = requests.get(
            self.source.config["api_url"],
            impersonate="chrome",
            timeout=30,
            headers={
                "accept": "application/json",
                "x-api-key": self.source.config["search_api_key"],
                "user-agent": self.source.config.get(
                    "user_agent",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36",
                ),
            },
        )
        response.raise_for_status()
        data = response.json()
        placards = data.get("data", {}).get("placards", [])
        if not isinstance(placards, list):
            raise ValueError("NEU aptsearch response did not contain placards")
        return [placard for placard in placards if isinstance(placard, dict)]

    def _normalize(self, placard: dict[str, Any]) -> NormalizedListing | None:
        site_id = str(placard.get("siteId") or "").strip()
        title = self._trim(str(placard.get("name") or "").strip(), 80)
        profile_url = str(placard.get("profileUrl") or "").strip()
        if not site_id or not title or not profile_url:
            return None

        site = self.source.config.get("site_url", "https://aptsearch.northeastern.edu").rstrip("/")
        source_url = profile_url if profile_url.startswith("http") else f"{site}{profile_url}"
        geography = placard.get("geography") if isinstance(placard.get("geography"), dict) else {}
        floor_plan = (
            placard.get("floorPlanSummary", {}).get("matching", {})
            if isinstance(placard.get("floorPlanSummary"), dict)
            else {}
        )
        address = self._address(geography)
        lease = self._string_or_none(placard.get("standardLeaseTerm"))
        distance = self._distance(geography)
        tags = self._term_tags(placard)
        images = self._images(placard)

        return NormalizedListing(
            id=f"neu-aptsearch-{site_id}",
            title=title,
            description=self._description(title, address, placard, lease, distance),
            price=self._price(floor_plan, placard),
            location=self._location(geography),
            bedrooms=self._beds(floor_plan),
            bathrooms=1.0,
            platform=self.source.name,
            dateListed=self._date_listed(placard),
            imageUrl=images[0] if images else None,
            imageUrls=images,
            sourceUrl=source_url,
            sourceVettedUsers=self.source.vetted_users,
            school="Northeastern University",
            availabilityLabel=lease,
            termTags=tags,
            amenities=self._amenities(placard, tags),
            extraCosts=self._extra_costs(placard),
        )

    def _address(self, geography: dict[str, Any]) -> str:
        street = self._string_or_none(geography.get("streetAddress"))
        city = self._string_or_none(geography.get("cityName"))
        state = self._string_or_none(geography.get("stateCode"))
        zip_code = self._string_or_none(geography.get("zipCode"))
        parts = [part for part in (street, city, state, zip_code) if part]
        return ", ".join(parts)

    def _description(
        self,
        title: str,
        address: str,
        placard: dict[str, Any],
        lease: str | None,
        distance: str | None,
    ) -> str:
        pieces = [title]
        if address:
            pieces.append(address)
        total_price = self._string_or_none(placard.get("totalMonthlyPrice"))
        if total_price:
            pieces.append(total_price)
        if lease:
            pieces.append(lease)
        if distance:
            pieces.append(distance)
        if placard.get("isSharedSpace"):
            pieces.append("Shared housing")
        return self._trim(" - ".join(pieces), 280)

    def _price(self, floor_plan: dict[str, Any], placard: dict[str, Any]) -> int | None:
        total = self._string_or_none(placard.get("totalMonthlyPrice")) or ""
        match = re.search(r"\$\s*([\d,]{3,6})", total)
        if match:
            return int(match.group(1).replace(",", ""))

        price = floor_plan.get("price") if isinstance(floor_plan.get("price"), dict) else {}
        low = price.get("low")
        if isinstance(low, (int, float)):
            return int(low)
        return None

    def _location(self, geography: dict[str, Any]) -> str:
        city = self._string_or_none(geography.get("cityName"))
        state = self._string_or_none(geography.get("stateCode"))
        zip_code = self._string_or_none(geography.get("zipCode")) or ""
        if city == "Boston" and zip_code == "02120":
            return "Mission Hill, Boston, MA"
        if city == "Boston" and zip_code == "02135":
            return "Brighton, Boston, MA"
        if city == "Boston" and zip_code == "02115":
            return "Fenway, Boston, MA"
        if city and state:
            return f"{city}, {state}"
        return self.source.config.get("default_location", "Boston, MA")

    def _beds(self, floor_plan: dict[str, Any]) -> int:
        beds = floor_plan.get("beds") if isinstance(floor_plan.get("beds"), dict) else {}
        low = beds.get("low")
        if isinstance(low, (int, float)):
            return int(low)
        formatted = self._string_or_none(beds.get("formatted")) or ""
        if "studio" in formatted.lower():
            return 0
        match = re.search(r"\d+", formatted)
        return int(match.group(0)) if match else 1

    def _date_listed(self, placard: dict[str, Any]) -> str:
        updated = self._string_or_none(placard.get("lastUpdated"))
        if updated and re.match(r"\d{4}-\d{2}-\d{2}", updated):
            return updated[:10]
        return "1970-01-01"

    def _distance(self, geography: dict[str, Any]) -> str | None:
        target = geography.get("targetCollege") if isinstance(geography.get("targetCollege"), dict) else {}
        distance = target.get("distance")
        if isinstance(distance, (int, float)):
            return f"{distance:g} miles to Northeastern"
        return None

    def _term_tags(self, placard: dict[str, Any]) -> list[str]:
        tags = ["Official portal"]
        if placard.get("isSublet"):
            tags.append("Sublet")
        if placard.get("isSharedSpace"):
            tags.append("Shared housing")
        if self._string_or_none(placard.get("standardLeaseTerm")):
            tags.append("Lease term")
        return tags

    def _amenities(self, placard: dict[str, Any], tags: list[str]) -> list[str]:
        amenities = ["NEU aptsearch", *tags]
        title = str(placard.get("name") or "").lower()
        media_text = " ".join(
            str(item.get("caption") or "")
            for item in placard.get("mediaCollection", [])
            if isinstance(item, dict)
        ).lower()
        keyword_labels = {
            "furnished": "Furnished",
            "no broker fee": "No broker fee",
            "virtual": "Virtual tour",
            "bedroom": "Bedroom",
        }
        searchable = f"{title} {media_text}"
        for keyword, label in keyword_labels.items():
            if keyword in searchable and label not in amenities:
                amenities.append(label)
        return amenities[:8]

    def _extra_costs(self, placard: dict[str, Any]) -> list[str]:
        total = (self._string_or_none(placard.get("totalMonthlyPrice")) or "").lower()
        return ["Fees mentioned"] if "fee" in total else []

    def _images(self, placard: dict[str, Any]) -> list[str]:
        images: list[str] = []
        for item in placard.get("mediaCollection", []):
            if not isinstance(item, dict):
                continue
            source = self._string_or_none(item.get("source"))
            if not source:
                continue
            if source.startswith("//"):
                source = f"https:{source}"
            if source.startswith("http") and source not in images:
                images.append(source)
        return images[:6]

    def _string_or_none(self, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _trim(self, value: str, limit: int) -> str:
        normalized = re.sub(r"\s+", " ", value or "").strip()
        if len(normalized) <= limit:
            return normalized
        return normalized[: limit - 1].rstrip() + "..."
