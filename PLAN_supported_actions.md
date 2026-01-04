# Add `supported_actions` Attribute to Pianobar Media Player

## Overview

Expose a `supported_actions` attribute on the Pianobar media player entity so that Lovelace cards can detect which song rating actions are available. This enables cards to conditionally show/hide rating controls based on entity capabilities.

---

## Problem

Currently, pianobar services (`love_song`, `ban_song`, `tired_of_song`) are registered globally. Cards have no way to determine if a specific media player entity supports these actions. This causes rating menus to appear on non-pianobar media players when the pianobar integration is installed.

---

## Solution

Add an `extra_state_attributes` property to the `PianobarMediaPlayer` class that exposes which actions the entity supports.

---

## Changes

### File: `custom_components/pianobar/media_player.py`

Add the `extra_state_attributes` property to the `PianobarMediaPlayer` class (after the existing properties, around line 142):

```python
@property
def extra_state_attributes(self) -> dict[str, Any]:
    """Return entity specific state attributes."""
    return {
        "supported_actions": [
            "love_song",
            "ban_song",
            "tired_of_song",
            "create_station",
            "rename_station",
            "delete_station",
            "reconnect",
        ],
    }
```

This will expose the attribute on the entity state, accessible via:

- Home Assistant Developer Tools: States
- `entity.attributes.supported_actions` in JavaScript/TypeScript
- Templates: `{{ state_attr('media_player.pianobar', 'supported_actions') }}`

---

## Expected Result

The pianobar media player entity will have an attribute:

```json
{
  "supported_actions": [
    "love_song",
    "ban_song",
    "tired_of_song",
    "create_station",
    "rename_station",
    "delete_station",
    "reconnect"
  ],
  "media_title": "...",
  "media_artist": "...",
  ...
}
```

Cards can then check:

```javascript
const supportedActions = entity.attributes.supported_actions || [];
const supportsLove = supportedActions.includes('love_song');
const supportsBan = supportedActions.includes('ban_song');
const supportsTired = supportedActions.includes('tired_of_song');
const supportsCreateStation = supportedActions.includes('create_station');
```

---

## Testing

1. Restart Home Assistant after making the change
2. Go to Developer Tools → States
3. Find the pianobar media player entity
4. Verify `supported_actions` appears in the attributes

