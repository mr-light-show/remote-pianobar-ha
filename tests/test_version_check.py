"""Test the player / integration version comparison."""
from __future__ import annotations

import json
import logging
from unittest.mock import patch

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from custom_components.pianobar.const import DOMAIN
from custom_components.pianobar.coordinator import PianobarCoordinator
from custom_components.pianobar.version_check import (
    MISSING,
    async_integration_version,
    parse_major,
    player_major,
    version_issue_id,
)

ENTRY_ID = "entry1"
ISSUE_ID = f"player_version_mismatch_{ENTRY_ID}"


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ("3.0.0", 3),
        ("3.0.0-dev.4", 3),
        ("v2.7.3", 2),
        ("10.1", 10),
        ("dev", None),
        ("garbage", None),
        ("", None),
        (3, None),
        (None, MISSING),
    ],
)
def test_player_major_parses_release_and_dev_tags(version, expected) -> None:
    """Release and dev tags give their major; anything else cannot be compared."""
    assert player_major(version) == expected


def test_parse_major_never_reports_missing() -> None:
    """The integration's own version is either parseable or not."""
    assert parse_major("1.0.3") == 1
    assert parse_major(None) is None
    assert parse_major("dev") is None


def test_version_issue_id_is_per_entry() -> None:
    """One issue per config entry."""
    assert version_issue_id(ENTRY_ID) == ISSUE_ID


async def test_integration_version_comes_from_manifest(hass: HomeAssistant) -> None:
    """The integration reads its own manifest version as a string."""
    version = await async_integration_version(hass)
    assert isinstance(version, str)
    assert parse_major(version) is not None


async def test_integration_version_none_without_manifest_version(
    hass: HomeAssistant,
) -> None:
    """A manifest without a version gives None."""
    class _NoVersion:
        version = None

    with patch(
        "custom_components.pianobar.version_check.async_get_integration",
        return_value=_NoVersion(),
    ):
        assert await async_integration_version(hass) is None


def _coordinator(hass: HomeAssistant, integration_version: str = "3.0.0"):
    return PianobarCoordinator(
        hass,
        "127.0.0.1",
        3000,
        entry_id=ENTRY_ID,
        integration_version=integration_version,
    )


def _process(version: str | None = None, *, with_field: bool = True) -> str:
    payload: dict = {"playing": False, "station": ""}
    if with_field:
        payload["version"] = version
    return "2" + json.dumps(["process", payload])


async def test_mismatch_creates_repairs_issue(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """A v2 player with a v3 integration raises one warning issue."""
    coordinator = _coordinator(hass)
    registry = ir.async_get(hass)

    with caplog.at_level(logging.WARNING):
        await coordinator._handle_message(_process("2.7.3"))
        # Further `process` events on the same connection do not log again
        await coordinator._handle_message(_process("2.7.3"))

    issue = registry.async_get_issue(DOMAIN, ISSUE_ID)
    assert issue is not None
    assert issue.severity == ir.IssueSeverity.WARNING
    assert issue.is_fixable is False
    assert issue.translation_key == "player_version_mismatch"
    assert issue.translation_placeholders == {
        "player_version": "2.7.3",
        "expected_major": "3",
    }
    warnings = [
        r for r in caplog.records
        if r.levelno == logging.WARNING and "2.7.3" in r.getMessage()
    ]
    assert len(warnings) == 1
    # Warn only: the connection's state is still used
    assert coordinator._initial_process_event.is_set()


async def test_mismatch_warns_again_on_next_connection(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """The once-per-connection warning is reset when connecting again."""
    coordinator = _coordinator(hass)
    await coordinator._handle_message(_process("2.7.3"))
    coordinator._reset_version_check()

    with caplog.at_level(logging.WARNING):
        await coordinator._handle_message(_process("2.7.3"))

    assert "2.7.3" in caplog.text


async def test_missing_version_field_warns_as_older_player(hass: HomeAssistant) -> None:
    """A `process` without `version` comes from a player older than v3."""
    coordinator = _coordinator(hass)

    await coordinator._handle_message(_process(with_field=False))

    issue = ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_ID)
    assert issue is not None
    assert issue.translation_placeholders == {
        "player_version": "< 3.0",
        "expected_major": "3",
    }


@pytest.mark.parametrize("version", ["dev", "garbage"])
async def test_dev_or_unparseable_version_does_not_warn(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture, version: str
) -> None:
    """A local build reports "dev": nothing to compare, debug log only."""
    coordinator = _coordinator(hass)

    with caplog.at_level(logging.DEBUG):
        await coordinator._handle_message(_process(version))

    assert ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_ID) is None
    assert not [r for r in caplog.records if r.levelno >= logging.WARNING]
    assert version in caplog.text


async def test_matching_major_clears_issue(hass: HomeAssistant) -> None:
    """Reaching a matching player (e.g. after a reconnect) deletes the issue."""
    coordinator = _coordinator(hass)
    registry = ir.async_get(hass)

    await coordinator._handle_message(_process("2.7.3"))
    assert registry.async_get_issue(DOMAIN, ISSUE_ID) is not None

    await coordinator._handle_message(_process("3.1.0"))
    assert registry.async_get_issue(DOMAIN, ISSUE_ID) is None


async def test_dev_player_clears_issue(hass: HomeAssistant) -> None:
    """A version that cannot be compared does not keep an old warning."""
    coordinator = _coordinator(hass)
    registry = ir.async_get(hass)

    await coordinator._handle_message(_process("2.7.3"))
    await coordinator._handle_message(_process("dev"))

    assert registry.async_get_issue(DOMAIN, ISSUE_ID) is None


async def test_stale_manifest_version_warns_against_v3_player(
    hass: HomeAssistant,
) -> None:
    """Until the release bump, the manifest's 1.0.3 warns against a v3 player."""
    coordinator = _coordinator(hass, integration_version="1.0.3")

    await coordinator._handle_message(_process("3.0.0"))

    issue = ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_ID)
    assert issue is not None
    assert issue.translation_placeholders == {
        "player_version": "3.0.0",
        "expected_major": "1",
    }


@pytest.mark.parametrize(
    ("entry_id", "integration_version"),
    [(None, "3.0.0"), (ENTRY_ID, None), (ENTRY_ID, "dev")],
)
async def test_no_check_without_entry_or_own_version(
    hass: HomeAssistant, entry_id: str | None, integration_version: str | None
) -> None:
    """Without a config entry or a comparable own version, nothing is checked."""
    coordinator = PianobarCoordinator(
        hass,
        "127.0.0.1",
        3000,
        entry_id=entry_id,
        integration_version=integration_version,
    )

    await coordinator._handle_message(_process("2.7.3"))

    assert ir.async_get(hass).issues == {}
