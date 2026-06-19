from __future__ import annotations

import hashlib
import html
import json
import re
import time
from pathlib import Path
from typing import Any

from scrapers.base import ListingScraper, NormalizedListing, SourceConfig
from scrapers.sources.reddit import RedditThreadScraper


ROOT = Path(__file__).resolve().parents[2]


class FacebookManualScraper(ListingScraper):
    """Normalize public Facebook group posts plus optional browser exports.

    Facebook's desktop page often redirects automation to login, but the mobile
    group route can expose a small public Comet payload. We scrape that first and
    fall back to a local JSON export when the public payload is unavailable or too
    limited. This avoids storing Facebook credentials or account cookies.
    """

    def __init__(self, source: SourceConfig) -> None:
        super().__init__(source)
        self.rules = RedditThreadScraper(source)

    def scrape(self) -> list[NormalizedListing]:
        max_items = int(self.source.config.get("max_items", 50))
        posts = self._fetch_public_posts()
        posts.extend(self._read_manual_posts())
        if not posts:
            return []

        listings: list[NormalizedListing] = []
        seen_keys: set[str] = set()
        for raw_post in posts:
            post = self._coerce_post(raw_post)
            if not post:
                continue

            listing = self._normalize_post(post)
            if listing is None:
                continue

            if listing.id in seen_keys:
                continue
            seen_keys.add(listing.id)
            listings.append(listing)
            if len(listings) >= max_items:
                break

        return listings

    def _read_manual_posts(self) -> list[dict[str, Any]]:
        input_path = ROOT / self.source.config.get(
            "input_path",
            "scrapers/manual/facebook_group_posts.json",
        )
        if not input_path.exists():
            print(f"Note: {self.source.name} skipped; no manual export at {input_path}")
            return []

        try:
            posts = json.loads(input_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"Warning: could not parse {self.source.name} export: {exc}")
            return []

        return posts if isinstance(posts, list) else []

    def _fetch_public_posts(self) -> list[dict[str, Any]]:
        public_url = self.source.config.get(
            "public_url",
            "https://m.facebook.com/groups/1464611414440265/",
        )
        candidate_urls = [
            public_url,
            f"{public_url.rstrip('/')}/?_rdr",
            self.source.config.get("group_url", ""),
        ]
        try:
            from curl_cffi import requests
        except Exception as exc:
            print(f"Warning: Facebook public preview requires curl_cffi: {exc}")
            return []

        last_url = public_url
        posts: list[dict[str, Any]] = []
        for attempt in range(3):
            for candidate_url in candidate_urls:
                if not candidate_url:
                    continue
                try:
                    response = requests.get(
                        candidate_url,
                        impersonate="chrome",
                        headers={
                            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                            "accept-language": "en-US,en;q=0.9",
                            "cache-control": "no-cache",
                        },
                        timeout=30,
                        allow_redirects=True,
                    )
                except Exception as exc:
                    print(f"Warning: could not fetch public Facebook group preview: {exc}")
                    continue

                last_url = response.url
                posts = self._extract_public_posts(response.text)
                if posts:
                    return posts
            time.sleep(1 + attempt)

        print(f"Warning: public Facebook group preview returned no posts from {last_url}")
        return posts

    def _extract_public_posts(self, page: str) -> list[dict[str, Any]]:
        posts: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        for match in re.finditer(r'"post_id":"(\d+)"', page):
            post_id = match.group(1)
            if post_id in seen_ids:
                continue

            chunk = page[max(0, match.start() - 3000) : min(len(page), match.end() + 14000)]
            text = self._decode_json_string_match(
                re.search(r'"text":"((?:\\.|[^"\\]){80,8000})"', chunk)
            )
            if not text:
                continue

            seen_ids.add(post_id)
            author = self._decode_json_string_match(
                re.search(r'"actors":\[\{"__typename":"User","name":"((?:\\.|[^"\\])+)","', chunk)
            )
            posts.append(
                {
                    "author": author,
                    "date": self.source.config.get("default_date", "2026-06-19"),
                    "url": f"{self.source.config.get('group_url', '').rstrip('/')}/posts/{post_id}/",
                    "text": text,
                    "imageUrls": self._extract_chunk_image_urls(chunk),
                }
            )
        return posts

    def _normalize_post(self, post: dict[str, Any]) -> NormalizedListing | None:
        text = post["text"]
        images = post["image_urls"]
        intent = self.rules._classify_intent(text, has_images=bool(images))
        if intent != "offer":
            return None

        price = self.rules._extract_price(text)
        location = self.rules._extract_location(text)
        availability = self.rules._extract_availability(text)
        title = self.rules._build_title(text, price, location, post["author"])
        listing_key = self._manual_listing_key(post["url"], post["author"], title, text)

        return NormalizedListing(
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

    def _decode_json_string_match(self, match: re.Match[str] | None) -> str:
        if not match:
            return ""
        try:
            return json.loads(f'"{match.group(1)}"')
        except json.JSONDecodeError:
            return ""

    def _extract_chunk_image_urls(self, chunk: str) -> list[str]:
        candidates = []
        candidates.extend(
            re.findall(r'https?:\\?/\\?/(?:\\.|[^"<>\\])+(?:jpg|jpeg|png|webp)(?:\\.|[^"<>\\])*', chunk)
        )
        candidates.extend(re.findall(r'https?://[^"<>]+(?:jpg|jpeg|png|webp)[^"<>]*', chunk))

        image_urls: list[str] = []
        for candidate in candidates:
            cleaned = candidate.replace("\\/", "/")
            cleaned = html.unescape(cleaned)
            if self._is_supported_image(cleaned) and cleaned not in image_urls:
                image_urls.append(cleaned)
        return image_urls[:6]

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
        if "s100x100" in lowered or "_nc_sid=e99d92" in lowered or "/t39.30808-1/" in lowered:
            return False
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
