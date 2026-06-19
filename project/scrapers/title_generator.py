from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

RESPONSES_URL = "https://api.openai.com/v1/responses"
MODEL = "gpt-5.4"


def generate_titles(listings: list[dict[str, Any]]) -> None:
    """Replace listing titles in place when an OpenAI API key is configured."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY is not set; keeping scraper-generated titles")
        return

    pending = [
        {"id": listing["id"], "description": listing["description"]}
        for listing in listings
        if listing.get("description")
    ]
    if not pending:
        return

    payload = {
        "model": MODEL,
        "reasoning": {"effort": "low"},
        "instructions": (
            "Write concise, specific titles for sublet listings. Base every title only "
            "on its description. Do not invent facts. Prefer location, room type, price, "
            "dates, or a standout amenity when explicitly present. Use title case, no "
            "quotation marks, no ending punctuation, and at most 60 characters. Return "
            "exactly one title for every supplied id."
        ),
        "input": json.dumps(pending, ensure_ascii=False),
        "text": {
            "format": {
                "type": "json_schema",
                "name": "sublet_titles",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "titles": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "title": {"type": "string"},
                                },
                                "required": ["id", "title"],
                                "additionalProperties": False,
                            },
                        }
                    },
                    "required": ["titles"],
                    "additionalProperties": False,
                },
            }
        },
        "max_output_tokens": max(1200, len(pending) * 40),
    }
    request = urllib.request.Request(
        RESPONSES_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            result = json.loads(response.read().decode("utf-8"))
        parsed = json.loads(_output_text(result))
    except (urllib.error.URLError, json.JSONDecodeError, KeyError, ValueError) as exc:
        print(f"Warning: OpenAI title generation failed; keeping existing titles: {exc}")
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


def _output_text(response: dict[str, Any]) -> str:
    chunks: list[str] = []
    for item in response.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                chunks.append(content.get("text", ""))
    if not chunks:
        raise ValueError("response did not contain output text")
    return "".join(chunks)
