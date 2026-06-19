from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from scrapers.base import ListingScraper, NormalizedListing, SourceConfig
from scrapers.sources.reddit import RedditThreadScraper


ROOT = Path(__file__).resolve().parents[2]


class FacebookManualScraper(ListingScraper):
    """Normalize Facebook group posts exported from a logged-in browser session.

    Facebook does not expose a reliable unauthenticated feed for public scheduled
    builds. This source intentionally reads a local JSON export instead of trying
    to automate login or store account cookies.
    """

    def __init__(self, source: SourceConfig) -> None:
        super().__init__(source)
        self.rules = RedditThreadScraper(source)

    def scrape(self) -> list[NormalizedListing]:
        input_path = ROOT / self.source.config.get(
            "input_path",
            "scrapers/manual/facebook_group_posts.json",
        )
        max_items = int(self.source.config.get("max_items", 50))
        if not input_path.exists():
            print(f"Note: {self.source.name} skipped; no manual export at {input_path}")
            return []

        try:
            posts = json.loads(input_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"Warning: could not parse {self.source.name} export: {exc}")
            return []

        listings: list[NormalizedListing] = []
        seen_keys: set[str] = set()
        for index, raw_post in enumerate(posts if isinstance(posts, list) else []):
            post = self._coerce_post(raw_post)
            if not post:
                continue

            text = post["text"]
            images = post["image_urls"]
            intent = self.rules._classify_intent(text, has_images=bool(images))
            if intent != "offer":
                continue

            price = self.rules._extract_price(text)
            location = self.rules._extract_location(text)
            availability = self.rules._extract_availability(text)
            title = self.rules._build_title(text, price, location, post["author"])
            listing_key = self._manual_listing_key(post["url"], post["author"], title, text)
            if listing_key in seen_keys:
                continue
            seen_keys.add(listing_key)

            listings.append(
                NormalizedListing(
                    id=f"facebook-{listing_key[:16]}",
                    title=title,
                    description=self.rules._trim(text, 320),
                    price=price,
                    location=location,
                    bedrooms=self.rules._extract_bedrooms(text),
                    bathrooms=self.rules._extract_bathrooms(text),
                    platform=self.source.name,
                    dateListed=post["date"],
                    imageUrl=images[0] if images else None,
                    imageUrls=images,
                    sourceUrl=post["url"] or self.source.config.get("group_url", ""),
                    sourceVettedUsers=self.source.vetted_users,
                    sourceAuthor=post["author"],
                    sourceIntent=intent,
                    availabilityLabel=availability["label"],
                    availableFrom=availability["from"],
                    availableTo=availability["to"],
                    termTags=availability["tags"],
                    amenities=self.rules._extract_amenities(text, "Facebook", "Facebook group"),
                    roommatesTotal=self.rules._extract_roommates(text),
                    parking=self.rules._extract_parking(text),
                    extraCosts=self.rules._extract_extra_costs(text),
                    utilitiesNotes=self.rules._extract_utilities(text),
                )
            )
            if len(listings) >= max_items:
                break

        return listings

    def _coerce_post(self, raw_post: Any) -> dict[str, Any] | None:
        if not isinstance(raw_post, dict):
            return None

        text = self._clean_text(str(raw_post.get("text") or raw_post.get("description") or ""))
        if not text:
            return None

        image_urls = raw_post.get("imageUrls") or raw_post.get("images") or []
        if not isinstance(image_urls, list):
            image_urls = []
        image_urls = [url for url in image_urls if isinstance(url, str) and self._is_supported_image(url)]

        return {
            "text": text,
            "author": self._clean_text(str(raw_post.get("author") or "")) or None,
            "date": self._normalize_date(str(raw_post.get("date") or raw_post.get("dateListed") or "")),
            "url": str(raw_post.get("url") or raw_post.get("sourceUrl") or "").strip(),
            "image_urls": image_urls[:6],
        }

    def _clean_text(self, text: str) -> str:
        cleaned = re.sub(r"\b(?:see more|view more|all reactions|comment|share)\b", " ", text, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def _normalize_date(self, value: str) -> str:
        match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", value)
        return match.group(1) if match else self.source.config.get("default_date", "2026-06-19")

    def _is_supported_image(self, url: str) -> bool:
        lowered = url.lower()
        return (
            lowered.startswith("https://")
            and (
                ".fbcdn.net/" in lowered
                or "scontent" in lowered
                or lowered.endswith((".jpg", ".jpeg", ".png", ".webp"))
            )
        )

    def _manual_listing_key(self, url: str, author: str | None, title: str, text: str) -> str:
        basis = url or f"{author or ''}:{title}:{self.rules._trim(text, 160)}"
        return hashlib.sha1(basis.encode("utf-8")).hexdigest()
