"""Tests for scripts/parse_recipe.py, exercised against the real captured example.

Run with either:
    python3 -m pytest tests/test_parse_recipe.py
    python3 tests/test_parse_recipe.py      # falls back to a plain assert runner
"""

import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from parse_recipe import parse_recipe, parse_recipe_description  # noqa: E402

EXAMPLE = REPO_ROOT / "examples" / "get-meals-recipe-redacted.json"


def test_parses_captured_recipe_example():
    payload = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    result = parse_recipe(payload)

    # 12 ingredient lines in the captured Mediterranean Chicken and Chickpea Bake.
    assert len(result["ingredients"]) == 12
    assert result["ingredients"][0] == (
        "2 boneless, skinless chicken thighs or breasts, cut into 1-inch pieces"
    )
    assert result["ingredients"][-1] == "Lemon wedges (for serving, optional)"

    # 6 numbered steps, with the "N." prefix stripped.
    assert len(result["instructions"]) == 6
    assert result["instructions"][0].startswith("Preheat oven")
    assert not result["instructions"][0][0].isdigit()
    assert result["instructions"][-1].startswith("Remove from oven")

    assert result["other"] == {}


def test_strips_varied_step_markers():
    text = "Instructions:\n1) First\nStep 2: Second\n- Third"
    result = parse_recipe_description(text)
    assert result["instructions"] == ["First", "Second", "Third"]


def test_header_synonyms_map_to_instructions():
    text = "Ingredients:\n1 egg\n\nDirections:\nFry it"
    result = parse_recipe_description(text)
    assert result["ingredients"] == ["1 egg"]
    assert result["instructions"] == ["Fry it"]


def test_headerless_blob_preserved_not_dropped():
    text = "Just some freeform notes\nwith two lines"
    result = parse_recipe_description(text)
    assert result["ingredients"] == []
    assert result["instructions"] == []
    assert result["other"]["body"] == ["Just some freeform notes", "with two lines"]


def test_empty_and_none_inputs():
    for value in (None, "", "   "):
        result = parse_recipe_description(value)
        assert result == {"ingredients": [], "instructions": [], "other": {}}


def _run_plain():
    """Minimal runner so the file works without pytest installed."""
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
        except AssertionError as exc:
            failures += 1
            print(f"FAIL {test.__name__}: {exc}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_run_plain())
