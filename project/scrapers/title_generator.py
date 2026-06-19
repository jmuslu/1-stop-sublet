from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any

MODEL = "gemini-1.5-flash-latest"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"


def generate_titles(listings: list[dict[str, Any]]) -> None:
    """Replace listing titles in place when a Gemini API key is configured."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY is not set; keeping scraper-generated titles")
        return

    pending = [
        {"id": listing["id"], "description": listing["description"]}
        for listing in listings
        if listing.get("description")
    ]
    if not pending:
        return

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "Write concise, specific titles for sublet listings. Base every "
                            "title only on its description. Do not invent facts. Prefer "
                            "location, room type, price, dates, or a standout amenity when "
                            "explicitly present. Use title case, no quotation marks, no "
                            "ending punctuation, and at most 60 characters. Return JSON "
                            "only in this shape: {\"titles\":[{\"id\":\"...\",\"title\":\"...\"}]}.\n\n"
                            f"Listings: {json.dumps(pending, ensure_ascii=False)}"
                        )
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "response_mime_type": "application/json",
        },
    }
    request = urllib.request.Request(
        f"{GEMINI_URL}?key={api_key}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            result = json.loads(response.read().decode("utf-8"))
        parsed = json.loads(_gemini_text(result))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, ValueError) as exc:
        print(f"Warning: Gemini title generation failed; keeping existing titles: {exc}")
        return

    titles = {
        item["id"]: item["title"].strip()
        for item in parsed.get("titles", [])
        if isinstance(item, dict)
        and isinstance(item.get("id"), str)
        and isinstance(item.get("title"), str)
        and 3 <= len(item["title"].strip()) <= 80
    }
    for listing in listings:
        generated = titles.get(listing["id"])
        if generated:
            listing["title"] = generated
            listing["titleGeneratedByAI"] = True

    print(f"Generated {len(titles)} of {len(pending)} listing titles with {MODEL}")


def _gemini_text(response: dict[str, Any]) -> str:
    text = (
        response.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [{}])[0]
        .get("text", "")
    )
    if not isinstance(text, str) or not text.strip():
        raise ValueError("response did not contain title JSON")
    return re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.IGNORECASE).strip()
