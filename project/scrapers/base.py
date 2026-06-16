from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SourceConfig:
    name: str
    enabled: bool
    vetted_users: bool
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class NormalizedListing:
    id: str
    title: str
    description: str
    price: int
    location: str
    bedrooms: int
    bathrooms: float
    platform: str
    dateListed: str
    imageUrl: str
    sourceUrl: str
    sourceVettedUsers: bool
    amenities: list[str] = field(default_factory=list)
    roommatesTotal: int | None = None
    floor: str | None = None
    parking: str | None = None
    extraCosts: list[str] = field(default_factory=list)
    utilitiesNotes: str | None = None
    applianceNotes: str | None = None

    def to_json(self) -> dict[str, Any]:
        payload = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "price": self.price,
            "location": self.location,
            "bedrooms": self.bedrooms,
            "bathrooms": self.bathrooms,
            "platform": self.platform,
            "dateListed": self.dateListed,
            "imageUrl": self.imageUrl,
            "sourceUrl": self.sourceUrl,
            "sourceVettedUsers": self.sourceVettedUsers,
            "amenities": self.amenities,
            "extraCosts": self.extraCosts,
        }
        optional = {
            "roommatesTotal": self.roommatesTotal,
            "floor": self.floor,
            "parking": self.parking,
            "utilitiesNotes": self.utilitiesNotes,
            "applianceNotes": self.applianceNotes,
        }
        payload.update({key: value for key, value in optional.items() if value is not None})
        return payload


class ListingScraper(ABC):
    def __init__(self, source: SourceConfig) -> None:
        self.source = source

    @abstractmethod
    def scrape(self) -> list[NormalizedListing]:
        """Return source listings normalized to the frontend listing contract."""
