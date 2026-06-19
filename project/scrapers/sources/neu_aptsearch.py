from __future__ import annotations

import html
import re
import urllib.error
import urllib.request
from typing import Any

from scrapers.base import ListingScraper, NormalizedListing

_TAG_RE = re.compile(r"<[^>]+>")
_PRICE_RE = re.compile(r"\$\s*([\d,]{3,6})")
_BED_RE = re.compile(r"(\d+)\s*(?:bed|beds|bedroom|bedrooms|br)\b", re.IGNORECASE)
_BATH_RE = re.compile(r"(\d+(?:\.5)?)\s*(?:bath|baths|bathroom|bathrooms|ba)\b", re.IGNORECASE)


class NeuAptSearchScraper(ListingScraper):
    """NEU aptsearch (https://aptsearch.northeastern.edu) — Northeastern's official
    off-campus housing portal, filtered to ``Sublets Only``.

    This is the university's own listing service, so listers are the building owners,
    property managers, and students who post through NU's portal. It is an *official*
    channel rather than a peer-verified one, so ``vetted_users`` is left false: we
    surface it as "official portal" rather than "verified student" in the UI.

    NOTE: as of this writing the portal sits behind Akamai bot protection and returns
    HTTP 403 ("Access Denied") to non-browser clients, so this source ships disabled
    (``"enabled": false`` in ``neu_aptsearch.json``). The scraper is wired and ready:
    enable it once requests are served through an approved browser/proxy path. Until
    then — and on any 403/network/parse failure — it prints a warning and returns
    ``[]`` so the build stays green and the previously generated data is kept.
    """

    def scrape(self) -> list[NormalizedListing]:
        cfg = self.source.config
        url = cfg["listings_url"]
        max_items = int(cfg.get("max_items", 100))

        try:
            page = self._fetch(url)
        except urllib.error.HTTPError as exc:
            if exc.code == 403:
                print(
                    f"Warning: {self.source.name} returned 403 (Akamai bot protection); "
                    "skipping. Enable via an approved browser/proxy path."
                )
            else:
                print(f"Warning: could not fetch {self.source.name}: {exc}")
            return []
        except urllib.error.URLError as exc:
            print(f"Warning: could not fetch {self.source.name}: {exc}")
            return []

        try:
            return self._parse(page)[:max_items]
        except (ValueError, KeyError) as exc:
            print(f"Warning: could not parse {self.source.name}: {exc}")
            return []

    def _fetch(self, url: str) -> str:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": self.source.config.get(
                    "user_agent",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", "replace")

    def _parse(self, page: str) -> list[NormalizedListing]:
        site = self.source.config.get(
            "site_url", "https://aptsearch.northeastern.edu"
        ).rstrip("/")
        anchor_re = re.compile(
            self.source.config.get("listing_href_pattern", r'href="(/listing[s]?/[^"#?]+)"'),
            re.IGNORECASE,
        )
        matches = list(anchor_re.finditer(page))
        listings: list[NormalizedListing] = []
        seen: set[str] = set()
        for index, match in enumerate(matches):
            href = match.group(1)
            if href in seen:
                continue
            seen.add(href)
            start = match.start()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(page)
            listing = self._normalize(href, page[start:end], site)
            if listing is not None:
                listings.append(listing)
        return listings

    def _normalize(self, href: str, segment: str, site: str) -> NormalizedListing | None:
        text = html.unescape(re.sub(r"\s+", " ", _TAG_RE.sub(" ", segment))).strip()
        if not text:
            return None

        listing_id = re.sub(r"[^a-zA-Z0-9]+", "-", href.strip("/"))
        source_url = href if href.startswith("http") else f"{site}{href}"
        price = self._price(text)
        title = self._trim(text, 80) or "Northeastern off-campus sublet"

        return NormalizedListing(
            id=f"neu-aptsearch-{listing_id}",
            title=title,
            description=self._trim(text, 280),
            price=price,
            location=self.source.config.get("default_location", "Boston, MA"),
            bedrooms=self._beds(text),
            bathrooms=self._baths(text),
            platform=self.source.name,
            dateListed="1970-01-01",
            imageUrl=self._image(segment),
            sourceUrl=source_url,
            sourceVettedUsers=self.source.vetted_users,
            amenities=["NEU aptsearch", "Official portal"],
        )

    def _price(self, text: str) -> int | None:
        match = _PRICE_RE.search(text)
        if not match:
            return None
        try:
            return int(match.group(1).replace(",", ""))
        except ValueError:
            return None

    def _beds(self, text: str) -> int:
        if re.search(r"\bstudio\b", text, re.IGNORECASE):
            return 0
        match = _BED_RE.search(text)
        return int(match.group(1)) if match else 1

    def _baths(self, text: str) -> float:
        match = _BATH_RE.search(text)
        return float(match.group(1)) if match else 1.0

    def _image(self, segment: str) -> str:
        match = re.search(r'src="(https?://[^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"', segment, re.IGNORECASE)
        if match:
            return match.group(1)
        return self.source.config.get("default_image_url", "")

    def _trim(self, value: str, limit: int) -> str:
        normalized = re.sub(r"\s+", " ", value or "").strip()
        if len(normalized) <= limit:
            return normalized
        return normalized[: limit - 1].rstrip() + "…"
