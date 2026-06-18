from __future__ import annotations

import html
import json
import os
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

from scrapers.base import ListingScraper, NormalizedListing

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.image_urls: list[str] = []
        self.link_urls: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "img" and values.get("src"):
            self.image_urls.append(values["src"])
        if tag == "a" and values.get("href"):
            self.link_urls.append(values["href"])

    def handle_data(self, data: str) -> None:
        cleaned = data.strip()
        if cleaned:
            self.parts.append(cleaned)

    def text(self) -> str:
        return " ".join(self.parts)


class RedditThreadScraper(ListingScraper):
    def scrape(self) -> list[NormalizedListing]:
        feed_url = self.source.config["feed_url"]
        max_items = int(self.source.config.get("max_items", 75))

        try:
            feed = self._fetch(feed_url)
        except urllib.error.URLError as exc:
            print(f"Warning: could not fetch {self.source.name}: {exc}")
            return []

        root = ET.fromstring(feed)
        thread_url = self.source.config["thread_url"].rstrip("/")
        thread_title = self.source.config.get("thread_title", "Housing megathread")
        subreddit = self.source.config.get("subreddit", "r/NEU")

        listings: list[NormalizedListing] = []
        seen_listing_keys: set[str] = set()
        seen_author_fingerprints: dict[str, list[set[str]]] = {}
        for entry in root.findall("atom:entry", ATOM_NS):
            link = self._entry_link(entry)
            if not link or link.rstrip("/") == thread_url:
                continue

            content, image_urls = self._entry_content(entry)
            intent = self._classify_intent(content, has_images=bool(image_urls))
            if intent != "offer":
                continue

            author = self._entry_author(entry)
            posted_at = self._entry_date(entry)
            price = self._extract_price(content)
            location = self._extract_location(content)
            bedrooms = self._extract_bedrooms(content)
            bathrooms = self._extract_bathrooms(content)
            title = self._build_title(content, price, location, author)
            amenities = self._extract_amenities(content, subreddit, thread_title)
            listing_key = self._listing_key(author, title)
            if listing_key in seen_listing_keys:
                continue
            fingerprint = self._listing_fingerprint(content)
            if self._is_near_duplicate(author, fingerprint, seen_author_fingerprints):
                continue
            seen_listing_keys.add(listing_key)
            seen_author_fingerprints.setdefault(author or "", []).append(fingerprint)

            listings.append(
                NormalizedListing(
                    id=f"reddit-{link.rstrip('/').split('/')[-1]}",
                    title=title,
                    description=self._trim(content, 280),
                    price=price,
                    location=location,
                    bedrooms=bedrooms,
                    bathrooms=bathrooms,
                    platform=self.source.name,
                    dateListed=posted_at,
                    imageUrl=image_urls[0] if image_urls else None,
                    imageUrls=image_urls,
                    sourceUrl=link,
                    sourceVettedUsers=self.source.vetted_users,
                    sourceSubreddit=subreddit,
                    sourceThreadTitle=thread_title,
                    sourceAuthor=author,
                    sourceIntent=intent,
                    amenities=amenities,
                    roommatesTotal=self._extract_roommates(content),
                    parking=self._extract_parking(content),
                    extraCosts=self._extract_extra_costs(content),
                    utilitiesNotes=self._extract_utilities(content),
                )
            )

            if len(listings) >= max_items:
                break

        return listings

    def _fetch(self, url: str) -> str:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": self.source.config.get(
                    "user_agent",
                    "Mozilla/5.0 1StopSublet/0.1 (housing aggregation)",
                )
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8")

    def _entry_link(self, entry: ET.Element) -> str | None:
        link = entry.find("atom:link", ATOM_NS)
        return link.attrib.get("href") if link is not None else None

    def _entry_author(self, entry: ET.Element) -> str | None:
        node = entry.find("atom:author/atom:name", ATOM_NS)
        return node.text if node is not None else None

    def _entry_date(self, entry: ET.Element) -> str:
        node = entry.find("atom:updated", ATOM_NS)
        if node is None or not node.text:
            return "1970-01-01"
        return node.text[:10]

    def _entry_content(self, entry: ET.Element) -> tuple[str, list[str]]:
        node = entry.find("atom:content", ATOM_NS)
        raw = node.text if node is not None and node.text else ""
        parser = _TextExtractor()
        decoded = html.unescape(raw)
        parser.feed(decoded)
        text = re.sub(r"\s+", " ", parser.text()).strip()
        return text, self._extract_image_urls(decoded, parser)

    def _classify_intent(self, text: str, has_images: bool) -> str:
        deterministic = self._classify_intent_with_rules(text, has_images)
        if deterministic != "unclear":
            return deterministic
        return self._classify_intent_with_gemini(text) or "seeker"

    def _classify_intent_with_rules(self, text: str, has_images: bool) -> str:
        lowered = text.lower().replace("’", "'")
        if any(term.lower() in lowered for term in self.source.config.get("exclude_terms", [])):
            return "seeker"
        if any(term.lower() in lowered for term in self.source.config.get("question_terms", [])):
            return "question"
        if any(term.lower() in lowered for term in self.source.config.get("seeker_terms", [])):
            return "seeker"
        if any(term.lower() in lowered for term in self.source.config.get("offer_terms", [])):
            return "offer"
        if has_images and any(term.lower() in lowered for term in self.source.config.get("include_terms", [])):
            return "offer"
        if any(term.lower() in lowered for term in self.source.config.get("include_terms", [])):
            return "unclear"
        return "seeker"

    def _classify_intent_with_gemini(self, text: str) -> str | None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return None
        prompt = (
            "Classify this Reddit housing megathread comment. "
            "Return exactly one word: offer, seeker, question, or irrelevant. "
            "Use offer only when the writer appears to have a room/unit/spot available. "
            f"Comment: {self._trim(text, 1200)}"
        )
        payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            "gemini-1.5-flash-latest:generateContent"
            f"?key={api_key}"
        )
        request = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            print(f"Warning: Gemini classification skipped: {exc}")
            return None
        text_value = (
            raw.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
            .strip()
            .lower()
        )
        if text_value.startswith("offer"):
            return "offer"
        if text_value.startswith("question"):
            return "question"
        if text_value.startswith("seeker") or text_value.startswith("irrelevant"):
            return "seeker"
        return None

    def _extract_image_urls(self, raw_html: str, parser: _TextExtractor) -> list[str]:
        candidates = parser.image_urls + parser.link_urls
        candidates += re.findall(r"https?://[^\s\"'<>]+", raw_html)
        image_urls: list[str] = []
        for candidate in candidates:
            cleaned = html.unescape(candidate).replace("&amp;", "&")
            if self._is_image_url(cleaned) and cleaned not in image_urls:
                image_urls.append(cleaned)
        return image_urls[:6]

    def _is_image_url(self, url: str) -> bool:
        lowered = url.lower()
        return (
            "preview.redd.it/" in lowered
            or "i.redd.it/" in lowered
            or lowered.endswith((".jpg", ".jpeg", ".png", ".webp"))
        )

    def _listing_key(self, author: str | None, text: str) -> str:
        normalized = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
        normalized = re.sub(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", "", normalized)
        return f"{author or ''}:{normalized[:90]}"

    def _listing_fingerprint(self, text: str) -> set[str]:
        normalized = text.lower().replace("’", "'")
        normalized = re.sub(r"\$?\b[0-9][0-9,]{1,5}\b(?:\s?\$)?", " ", normalized)
        tokens = set(re.findall(r"\b[a-z][a-z]{3,}\b", normalized))
        stop_words = {
            "apartment",
            "available",
            "please",
            "reach",
            "room",
            "rooms",
            "sublet",
            "subletting",
        }
        return tokens - stop_words

    def _is_near_duplicate(
        self,
        author: str | None,
        fingerprint: set[str],
        seen_author_fingerprints: dict[str, list[set[str]]],
    ) -> bool:
        if len(fingerprint) < 6:
            return False
        for existing in seen_author_fingerprints.get(author or "", []):
            overlap = len(fingerprint & existing)
            union = len(fingerprint | existing)
            if union and overlap / union >= 0.48:
                return True
        return False

    def _extract_price(self, text: str) -> int | None:
        patterns = [
            r"\$\s?([0-9][0-9,]{2,5})",
            r"\b([0-9][0-9,]{2,5})\s?\$",
            r"\b(?:rent|budget|price)\D{0,18}([0-9][0-9,]{2,5})\b",
            r"\b([0-9][0-9,]{2,5})\s?(?:/mo|per month|monthly)\b",
        ]
        matches: list[str] = []
        for pattern in patterns:
            matches.extend(re.findall(pattern, text, re.IGNORECASE))
        if not matches:
            return None
        prices = [int(match.replace(",", "")) for match in matches]
        plausible = [price for price in prices if 400 <= price <= 6000]
        return plausible[0] if plausible else None

    def _extract_location(self, text: str) -> str:
        for location in self.source.config.get("location_terms", []):
            if re.search(rf"\b{re.escape(location)}\b", text, re.IGNORECASE):
                return f"{location}, Boston, MA"
        return self.source.config.get("default_location", "Boston, MA")

    def _extract_bedrooms(self, text: str) -> int:
        patterns = [
            r"\b([1-6])\s?(?:bed|beds|bedroom|bedrooms|br)\b",
            r"\b([1-6])b(?:d|r)?\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        if re.search(r"\bstudio\b", text, re.IGNORECASE):
            return 0
        return 1

    def _extract_bathrooms(self, text: str) -> float:
        match = re.search(r"\b([1-4](?:\.5)?)\s?(?:bath|baths|bathroom|bathrooms|ba)\b", text, re.IGNORECASE)
        return float(match.group(1)) if match else 1

    def _extract_roommates(self, text: str) -> int | None:
        match = re.search(r"\b(?:with|and)\s+([1-6])\s+(?:roommates|people|others)\b", text, re.IGNORECASE)
        if match:
            return int(match.group(1)) + 1
        match = re.search(r"\b([1-6])\s+(?:roommates|people)\b", text, re.IGNORECASE)
        return int(match.group(1)) if match else None

    def _extract_parking(self, text: str) -> str | None:
        lowered = text.lower()
        if "parking" not in lowered and "driveway" not in lowered:
            return None
        if "no parking" in lowered:
            return "No parking listed"
        if "driveway" in lowered:
            return "Driveway access"
        return "Parking mentioned"

    def _extract_extra_costs(self, text: str) -> list[str]:
        costs = []
        lowered = text.lower()
        if "utilities" in lowered:
            costs.append("Utilities mentioned")
        if "fee" in lowered:
            costs.append("Fees mentioned")
        return costs

    def _extract_utilities(self, text: str) -> str | None:
        sentence = self._sentence_containing(text, "utilities")
        return self._trim(sentence, 140) if sentence else None

    def _extract_amenities(self, text: str, subreddit: str, thread_title: str) -> list[str]:
        amenities = ["Reddit", subreddit]
        lowered = text.lower()
        keyword_labels = {
            "furnished": "Furnished",
            "laundry": "Laundry",
            "parking": "Parking",
            "driveway": "Driveway",
            "gym": "Gym",
            "near": "Near campus",
            "co-op": "Co-op term",
            "sublet": "Sublet",
            "roommate": "Roommate",
        }
        for keyword, label in keyword_labels.items():
            if keyword in lowered and label not in amenities:
                amenities.append(label)
        if thread_title and "Housing megathread" not in amenities:
            amenities.append("Housing megathread")
        return amenities[:6]

    def _build_title(self, text: str, price: int | None, location: str, author: str | None) -> str:
        if price and location != self.source.config.get("default_location", "Boston, MA"):
            return f"${price:,} housing lead near {location.replace(', Boston, MA', '')}"
        title = self._best_title_sentence(text)
        if title:
            return title
        return f"Reddit housing lead from {author or 'r/NEU'}"

    def _best_title_sentence(self, text: str) -> str:
        generic = {
            "hi",
            "hi!",
            "hi everyone",
            "hi everyone!",
            "hello",
            "hello!",
            "hey",
            "hey!",
            "hey everyone",
            "hey everyone!",
        }
        sentences = re.split(r"(?<=[.!?])\s+", text)
        for sentence in sentences:
            cleaned = sentence.strip()
            if cleaned.lower() in generic:
                continue
            if len(cleaned) < 8:
                continue
            return self._trim(cleaned, 72)
        return ""

    def _sentence_containing(self, text: str, term: str) -> str | None:
        for sentence in re.split(r"(?<=[.!?])\s+", text):
            if term.lower() in sentence.lower():
                return sentence
        return None

    def _trim(self, value: str | None, limit: int) -> str:
        if not value:
            return ""
        normalized = re.sub(r"\s+", " ", value).strip()
        if len(normalized) <= limit:
            return normalized
        return normalized[: limit - 1].rstrip() + "..."
