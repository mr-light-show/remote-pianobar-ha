# Pandora Media Player for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/release/mr-light-show/remote-pianobar-ha.svg)](https://github.com/mr-light-show/remote-pianobar-ha/releases)
[![Test](https://github.com/mr-light-show/remote-pianobar-ha/workflows/Test/badge.svg)](https://github.com/mr-light-show/remote-pianobar-ha/actions)
[![codecov](https://codecov.io/gh/mr-light-show/remote-pianobar-ha/branch/main/graph/badge.svg)](https://codecov.io/gh/mr-light-show/remote-pianobar-ha)

A Home Assistant integration for controlling [remote-pianobar](https://github.com/mr-light-show/remote-pianobar) - a WebSocket-enabled Pandora client.

## Features

- 🎵 Full media player controls (play, pause, next track)
- 🔊 Volume control with perceptual curve mapping
- 📻 Station management and quick switching
- 🔍 Browse and search for new music/stations
- 👍 Pandora-specific actions (love, ban, tired of song)
- 🎨 Album artwork display
- 🤖 Automation-friendly with `play_media` support

## Prerequisites

You need a running instance of [remote-pianobar](https://github.com/mr-light-show/remote-pianobar) with WebSocket support.

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner and select "Custom repositories"
4. Add this repository URL and select "Integration" as the category
5. Click "Install" on the Pianobar card
6. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/pianobar` directory to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Pianobar"
4. Enter your remote-pianobar host and port (default: 8080)

## Usage

### Basic Controls

Use the standard media player card in your dashboard to control playback:

```yaml
type: media-control
entity: media_player.pianobar
```

### Selecting Stations

Stations appear in the source dropdown. You can also use automations:

```yaml
service: media_player.select_source
target:
  entity_id: media_player.pianobar
data:
  source: "Today's Hits Radio"
```

Or use `play_media`:

```yaml
service: media_player.play_media
target:
  entity_id: media_player.pianobar
data:
  media_content_type: station
  media_content_id: "3914377188324099182"  # Station ID
```

### Custom Services

#### Love Current Song

```yaml
service: pianobar.love_song
target:
  entity_id: media_player.pianobar
```

#### Ban Current Song

```yaml
service: pianobar.ban_song
target:
  entity_id: media_player.pianobar
```

#### Tired of Song

```yaml
service: pianobar.tired_of_song
target:
  entity_id: media_player.pianobar
```

#### Create Station from Current Song

```yaml
service: pianobar.create_station
target:
  entity_id: media_player.pianobar
data:
  type: song  # or "artist"
```

#### Explain Song

Get Pandora's explanation for why the current song was chosen:

```yaml
service: pianobar.explain_song
target:
  entity_id: media_player.pianobar
response_variable: explanation
```

#### Get Upcoming Songs

Get list of upcoming songs in the queue:

```yaml
service: pianobar.get_upcoming
target:
  entity_id: media_player.pianobar
response_variable: upcoming
```

#### Set QuickMix

Configure which stations are included in QuickMix:

```yaml
service: pianobar.set_quick_mix
target:
  entity_id: media_player.pianobar
data:
  station_ids:
    - "3914377188324099182"
    - "4506787012345678901"
```

#### Add Seed to Station

Add an artist or song as a seed to an existing station (requires musicId from search):

```yaml
service: pianobar.add_seed
target:
  entity_id: media_player.pianobar
data:
  music_id: "R12345"
  station_id: "3914377188324099182"
```

#### Get Station Info

Get station seeds and feedback history:

```yaml
service: pianobar.get_station_info
target:
  entity_id: media_player.pianobar
data:
  station_id: "3914377188324099182"
response_variable: station_info
```

#### Delete Seed from Station

Remove a seed from a station:

```yaml
service: pianobar.delete_seed
target:
  entity_id: media_player.pianobar
data:
  seed_id: "AS1234567890"
  seed_type: "artist"  # or "song" or "station"
  station_id: "3914377188324099182"
```

#### Delete Feedback

Remove a thumbs up/down from station history:

```yaml
service: pianobar.delete_feedback
target:
  entity_id: media_player.pianobar
data:
  feedback_id: "F9988776655"
  station_id: "3914377188324099182"
```

#### Get Station Modes

Get available playback modes for a station (My Station, Crowd Faves, Deep Cuts, Discovery):

```yaml
service: pianobar.get_station_modes
target:
  entity_id: media_player.pianobar
data:
  station_id: "3914377188324099182"
response_variable: modes
```

#### Set Station Mode

Set the playback mode for a station:

```yaml
service: pianobar.set_station_mode
target:
  entity_id: media_player.pianobar
data:
  station_id: "3914377188324099182"
  mode_id: 2  # 0=My Station, 1=Crowd Faves, 2=Deep Cuts, 3=Discovery
```

#### Toggle Playback

Toggle between play and pause:

```yaml
service: pianobar.toggle_playback
target:
  entity_id: media_player.pianobar
```

#### Reset Volume

Reset volume to 50% default:

```yaml
service: pianobar.reset_volume
target:
  entity_id: media_player.pianobar
```

#### Search for Music

Search for artists and songs to create stations:

```yaml
service: pianobar.search
target:
  entity_id: media_player.pianobar
data:
  query: "The Beatles"
response_variable: search_results
```

Returns search results with categories for Artists and Songs, each containing musicId values for creating stations.

#### Get Genre Categories

Get available genre categories for creating genre-based stations:

```yaml
service: pianobar.get_genres
target:
  entity_id: media_player.pianobar
response_variable: genres
```

Returns genre categories (Rock, Pop, Jazz, etc.) with musicId values for each genre.

#### Create Station from Music ID

Create a new station from a search result or genre (uses musicId from search or get_genres):

```yaml
service: pianobar.create_station_from_music_id
target:
  entity_id: media_player.pianobar
data:
  music_id: "R12345"  # From search results or genre list
```

#### Add Shared Station

Add a shared station using its numeric ID from a Pandora share link:

```yaml
service: pianobar.add_shared_station
target:
  entity_id: media_player.pianobar
data:
  station_id: "1234567890"  # Numeric ID from pandora.com/station/1234567890
```

## Media Browser

Browse your stations and search for new music using the built-in media browser:

1. Click on the media player card
2. Click "Browse Media"
3. Navigate through your stations or search for new music

## Entity Attributes

The media player entity exposes additional attributes for Lovelace card integration:

### `supported_actions`

Array of custom actions this entity supports:
- `love_song`, `ban_song`, `tired_of_song` - Song rating actions
- `create_station`, `rename_station`, `delete_station` - Station management
- `reconnect` - WebSocket reconnection
- `explain_song` - Get song recommendation explanation
- `get_upcoming` - View upcoming songs in queue
- `set_quick_mix` - Configure QuickMix stations
- `add_seed`, `delete_seed` - Station seed management
- `delete_feedback` - Remove rating from station
- `get_station_info` - Get station details
- `get_station_modes`, `set_station_mode` - Station playback modes
- `toggle_playback` - Toggle play/pause
- `reset_volume` - Reset volume to default
- `search` - Search for artists and songs
- `get_genres` - Get genre categories
- `create_station_from_music_id` - Create station from search/genre result
- `add_shared_station` - Add shared station by ID

### `rating`

Current song's rating:
- `0` = Not rated
- `1` = Loved (thumbs up)

### Example Usage (Templates)

```yaml
# Check if song is loved
{{ state_attr('media_player.pianobar', 'rating') == 1 }}

# Check if action is supported
{{ 'love_song' in state_attr('media_player.pianobar', 'supported_actions') }}
```

### Example Usage (JavaScript/Cards)

```javascript
const supportedActions = entity.attributes.supported_actions || [];
const supportsLove = supportedActions.includes('love_song');
const isLoved = entity.attributes.rating === 1;
```

## Supported Features

- ✅ Play/Pause
- ✅ Next Track
- ✅ Volume Control (set & step)
- ✅ Station Selection (source)
- ✅ Browse Media
- ✅ Play Media (automations)
- ❌ Seek (Pandora streaming limitation)
- ❌ Previous Track (Pandora limitation)
- ❌ Shuffle/Repeat (inherent to Pandora)

## Troubleshooting

### Connection Issues

- Verify remote-pianobar is running and accessible
- Check the host and port in the integration configuration
- Ensure WebSocket support is enabled in remote-pianobar

### No Stations Showing

- Make sure you're logged into Pandora in pianobar
- Try restarting the integration

## Development

### Running Tests

To run the test suite locally:

```bash
# Install test dependencies
pip install -r requirements_test.txt

# Run all tests
pytest tests/

# Run tests with coverage
pytest tests/ --cov=custom_components/pianobar --cov-report=term-missing

# Run specific test file
pytest tests/test_media_player.py

# Run specific test
pytest tests/test_media_player.py::test_media_player_state_playing
```

### Test Coverage

The integration includes comprehensive tests for:
- **Config Flow**: Connection validation and setup
- **Coordinator**: WebSocket communication and event handling
- **Media Player**: All media player controls and state management
- **Browse Media**: Station browsing functionality
- **Integration Setup**: Service registration and lifecycle
- **Volume Conversions**: dB to percentage mappings

### CI/CD

GitHub Actions automatically runs tests on:
- Python 3.11 and 3.12
- Every push and pull request
- Code coverage is tracked and reported

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

When contributing:
1. Write tests for new features
2. Ensure all tests pass (`pytest tests/`)
3. Follow Home Assistant coding standards
4. Update documentation as needed

## License

MIT License - see LICENSE file for details

## Credits

- [remote-pianobar](https://github.com/mr-light-show/remote-pianobar) - WebSocket-enabled Pandora client
- [pianobar](https://github.com/PromyLOPh/pianobar) - Original command-line Pandora client

