#!/usr/bin/env python3
"""Parse a Skylight ``meal_recipe`` description blob into structured data.

Skylight recipes are **not** machine-structured: the API returns the whole recipe
as a single free-text ``description`` attribute, by convention laid out as::

    Ingredients:
    <one ingredient per line>
    ...

    Instructions:
    1. <step>
    2. <step>
    ...

This module turns that text into ``{"ingredients": [...], "instructions": [...]}``
so meal-planning automation can work with the parts instead of the blob.

It is deliberately tolerant: header matching is case-insensitive, a few common
synonyms are recognised (Directions/Method/Steps/Notes), list bullets and step
numbering are stripped, and unrecognised sections are preserved under ``other`` so
nothing is silently dropped. If no recognisable headers are present, the entire
text is returned as a single ``ingredients``-less block under ``other["body"]``.

CLI::

    python3 scripts/parse_recipe.py examples/get-meals-recipe-redacted.json
    echo "Ingredients:\n1 egg\n\nInstructions:\n1. Fry it" | python3 scripts/parse_recipe.py --text -
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any

# Header line -> canonical bucket. Matched case-insensitively against a whole line
# that is just the header (optionally followed by a colon).
_HEADER_ALIASES = {
    "ingredients": "ingredients",
    "instructions": "instructions",
    "directions": "instructions",
    "method": "instructions",
    "preparation": "instructions",
    "prep": "instructions",
    "steps": "instructions",
    "notes": "notes",
    "note": "notes",
}

_HEADER_RE = re.compile(r"^\s*([A-Za-z][A-Za-z ]*?)\s*:?\s*$")

# Leading list decoration to strip from an item: "1.", "1)", "12 -", "- ", "* ",
# "•", "Step 3:", etc.
_LEADING_MARKER_RE = re.compile(
    r"^\s*(?:step\s+\d+\s*[:.)-]?\s*|\d+\s*[.)\-:]\s*|[-*•]\s+)",
    re.IGNORECASE,
)


def _canonical_header(line: str) -> str | None:
    """Return the canonical bucket name if ``line`` is a recognised header, else None."""
    match = _HEADER_RE.match(line)
    if not match:
        return None
    return _HEADER_ALIASES.get(match.group(1).strip().lower())


def _clean_item(line: str) -> str:
    """Strip leading bullets/step numbering and surrounding whitespace."""
    return _LEADING_MARKER_RE.sub("", line).strip()


def parse_recipe_description(text: str | None) -> dict[str, Any]:
    """Parse a recipe ``description`` blob into structured sections.

    Returns a dict with keys:
      - ``ingredients``: list[str] (one entry per ingredient line)
      - ``instructions``: list[str] (step numbering stripped)
      - ``other``: dict[str, list[str]] for any unrecognised sections; when the text
        has no recognisable headers at all, the full text lands in ``other["body"]``.
    """
    result: dict[str, Any] = {"ingredients": [], "instructions": [], "other": {}}
    if not text:
        return result

    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    # Bucket key for lines seen before any header. Kept separate so a header-less
    # blob is preserved rather than dropped.
    current: str | None = None
    preamble: list[str] = []

    for raw_line in lines:
        header = _canonical_header(raw_line)
        if header is not None:
            current = header
            if header in ("ingredients", "instructions"):
                result.setdefault(header, [])
            else:
                result["other"].setdefault(header, [])
            continue

        stripped = raw_line.strip()
        if not stripped:
            continue

        if current is None:
            preamble.append(stripped)
        elif current in ("ingredients", "instructions"):
            item = _clean_item(raw_line) if current == "instructions" else stripped
            if item:
                result[current].append(item)
        else:
            result["other"][current].append(_clean_item(raw_line) or stripped)

    if preamble:
        # No header preceded this text. If nothing else was parsed, treat the whole
        # thing as an unstructured body; otherwise keep it as a labelled preamble.
        if not result["ingredients"] and not result["instructions"] and not result["other"]:
            result["other"]["body"] = preamble
        else:
            result["other"].setdefault("preamble", []).extend(preamble)

    return result


def _extract_description(payload: Any) -> str | None:
    """Pull a recipe ``description`` string out of the various shapes we accept.

    Supports: a raw string; an attributes dict ``{"description": ...}``; a resource
    ``{"attributes": {...}}``; an API response ``{"data": {"attributes": {...}}}``;
    and a captured example ``{"response": {"body": {"data": {...}}}}``.
    """
    if isinstance(payload, str):
        return payload
    if not isinstance(payload, dict):
        return None

    node: Any = payload
    for key in ("response", "body"):
        if isinstance(node, dict) and key in node:
            node = node[key]
    if isinstance(node, dict) and "data" in node:
        node = node["data"]
    # ``data`` may be a single resource or a list; take the first resource.
    if isinstance(node, list):
        node = node[0] if node else {}
    if isinstance(node, dict) and "attributes" in node:
        node = node["attributes"]
    if isinstance(node, dict):
        desc = node.get("description")
        return desc if isinstance(desc, str) else None
    return None


def parse_recipe(payload: Any) -> dict[str, Any]:
    """Parse a recipe from any accepted shape (see :func:`_extract_description`)."""
    return parse_recipe_description(_extract_description(payload))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "source",
        nargs="?",
        help="Path to a JSON file (captured example, API response, or resource). "
        "Omit to read JSON from stdin.",
    )
    parser.add_argument(
        "--text",
        metavar="FILE",
        help="Treat input as raw recipe text instead of JSON. Use '-' for stdin.",
    )
    args = parser.parse_args(argv)

    if args.text is not None:
        raw = sys.stdin.read() if args.text == "-" else open(args.text, encoding="utf-8").read()
        result = parse_recipe_description(raw)
    else:
        raw = sys.stdin.read() if args.source in (None, "-") else open(args.source, encoding="utf-8").read()
        result = parse_recipe(json.loads(raw))

    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
