"""Compare the player's major version with this integration's.

The player (v3 and later) sends its version in the `process` event: a release
sets it from its tag (e.g. "3.0.0"), a local build sends "dev". Older players
send no version. A mismatch is a warning only, never a reason to refuse.
"""
from __future__ import annotations

import re
from typing import Any, Final, Literal

from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from .const import DOMAIN

# `player_major` result for a `process` event without a version field
MISSING: Final = "missing"
# Shown as the player version for a player too old to send one (the field
# arrived in v3.0.0)
OLDER_PLAYER_VERSION: Final = "< 3.0"
ISSUE_TRANSLATION_KEY: Final = "player_version_mismatch"

_MAJOR_RE = re.compile(r"v?(\d+)(?:\.\d+)*(?:[-+].*)?")


def parse_major(version: Any) -> int | None:
    """Return the major of a version like "3.0.0", "v2.7.3" or "3.0.0-dev.4".

    None for anything else, such as "dev".
    """
    if not isinstance(version, str):
        return None
    match = _MAJOR_RE.fullmatch(version.strip())
    return int(match.group(1)) if match else None


def player_major(version: Any) -> int | None | Literal["missing"]:
    """Return the player's major version, MISSING when it sent none, or None
    when it cannot be compared."""
    if version is None:
        return MISSING
    return parse_major(version)


def version_issue_id(entry_id: str) -> str:
    """Return the Repairs issue id for a config entry."""
    return f"{ISSUE_TRANSLATION_KEY}_{entry_id}"


async def async_integration_version(hass: HomeAssistant) -> str | None:
    """Return this integration's version from manifest.json."""
    integration = await async_get_integration(hass, DOMAIN)
    return str(integration.version) if integration.version else None
