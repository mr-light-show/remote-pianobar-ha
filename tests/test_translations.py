"""Check translations/en.json against the translation keys the code uses."""
from __future__ import annotations

import ast
import json
from pathlib import Path

from custom_components.pianobar import version_check

PACKAGE = Path(__file__).parent.parent / "custom_components" / "pianobar"
EN = json.loads((PACKAGE / "translations" / "en.json").read_text(encoding="utf-8"))

# Top-level sections hassfest accepts that this integration uses
DOCUMENTED_TOP_LEVEL = {
    "title",
    "config",
    "options",
    "entity",
    "device",
    "common",
    "exceptions",
    "issues",
    "services",
}

# Names the code passes as a translation key instead of a literal
KNOWN_NAMES = {"ISSUE_TRANSLATION_KEY": version_check.ISSUE_TRANSLATION_KEY}


def _strings(node: ast.AST) -> set[str]:
    """Return every literal or known-constant string in an expression."""
    found = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            found.add(sub.value)
        elif isinstance(sub, ast.Name) and sub.id in KNOWN_NAMES:
            found.add(KNOWN_NAMES[sub.id])
    return found


def _used_keys() -> dict[str, set[str]]:
    """Return translation keys used in code, by en.json section."""
    used: dict[str, set[str]] = {"exceptions": set(), "issues": set()}
    for path in PACKAGE.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
            section = "issues" if name == "async_create_issue" else "exceptions"
            for keyword in node.keywords:
                if keyword.arg == "translation_key":
                    used[section] |= _strings(keyword.value)
            # Failures stored for a waiting service become exceptions
            if name == "_ResponseFailure" and node.args:
                used["exceptions"] |= _strings(node.args[0])
    return used


def test_en_json_has_only_documented_top_level_keys() -> None:
    """hassfest rejects ad hoc top-level sections."""
    assert set(EN) <= DOCUMENTED_TOP_LEVEL


def test_every_translation_key_used_in_code_exists() -> None:
    """Every exception and Repairs key the code raises has English text."""
    used = _used_keys()
    assert "player_version_mismatch" in used["issues"]
    assert "request_too_large" in used["exceptions"]
    for key in used["exceptions"]:
        assert "message" in EN["exceptions"].get(key, {}), key
    for key in used["issues"]:
        assert {"title", "description"} <= set(EN["issues"].get(key, {})), key


def test_version_issue_placeholders_match_text() -> None:
    """The Repairs text uses exactly the placeholders the coordinator sends."""
    description = EN["issues"]["player_version_mismatch"]["description"]
    assert "{player_version}" in description
    assert "{expected_major}" in description
