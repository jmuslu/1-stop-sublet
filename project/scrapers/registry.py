from __future__ import annotations

import json
from pathlib import Path

from scrapers.base import ListingScraper, SourceConfig
from scrapers.sources.seed import SeedListingScraper

ROOT = Path(__file__).resolve().parent
SOURCES_DIR = ROOT / "sources"

SCRAPER_TYPES: dict[str, type[ListingScraper]] = {
    "seed": SeedListingScraper,
}


def load_sources() -> list[ListingScraper]:
    scrapers: list[ListingScraper] = []
    for config_path in sorted(SOURCES_DIR.glob("*.json")):
        raw = json.loads(config_path.read_text(encoding="utf-8"))
        scraper_type = raw.pop("type")
        scraper_class = SCRAPER_TYPES[scraper_type]
        source = SourceConfig(
            name=raw["name"],
            enabled=raw.get("enabled", True),
            vetted_users=raw.get("vetted_users", False),
            config=raw.get("config", {}),
        )
        if source.enabled:
            scrapers.append(scraper_class(source))
    return scrapers
