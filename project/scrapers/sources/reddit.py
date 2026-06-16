from __future__ import annotations

import html
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
        default_image_url = self.source.config["default_image_url"]

        listings: list[NormalizedListing] = []
        for entry in root.findall("atom:entry", ATOM_NS):
            link = self._entry_link(entry)
            if not link or link.rstrip("/") == thread_url:
                continue

            content = self._entry_text(entry)
            if not self._looks_like_housing_post(content):
                continue

            author = self._entry_author(entry)
            posted_at = self._entry_date(entry)
            price = self._extract_price(content)
            location = self._extract_location(content)
            bedrooms = self._extract_bedrooms(content)
            bathrooms = self._extract_bathrooms(content)
            title = self._build_title(content, price, location, author)
            amenities = self._extract_amenities(content, subreddit, thread_title)

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
                    imageUrl=default_image_url,
                    sourceUrl=link,
                    sourceVettedUsers=self.source.vetted_users,
                    sourceSubreddit=subreddit,
                    sourceThreadTitle=thread_title,
                    sourceAuthor=author,
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

    def _entry_text(self, entry: ET.Element) -> str:
        node = entry.find("atom:content", ATOM_NS)
        raw = node.text if node is not None and node.text else ""
        parser = _TextExtractor()
        parser.feed(html.unescape(raw))
        return re.sub(r"\s+", " ", parser.text()).strip()

    def _looks_like_housing_post(self, text: str) -> bool:
        lowered = text.lower()
        include_terms = self.source.config.get("include_terms", [])
        exclude_terms = self.source.config.get("exclude_terms", [])
        if any(term.lower() in lowered for term in exclude_terms):
            return False
        return any(term.lower() in lowered for term in include_terms)

    def _extract_price(self, text: str) -> int | None:
        matches = re.findall(r"\$\s?([0-9][0-9,]{2,5})", text)
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
        generic = {"hi", "hi!", "hello", "hello!", "hey", "hey!"}
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
