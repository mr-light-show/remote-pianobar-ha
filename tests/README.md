# Pianobar Integration Tests

This directory contains comprehensive tests for the Pianobar Home Assistant integration.

## Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Shared pytest fixtures
├── test_config_flow.py      # Configuration flow tests
├── test_coordinator.py      # WebSocket coordinator tests
├── test_media_player.py     # Media player entity tests
├── test_browse_media.py     # Browse media tests
└── test_init.py             # Integration setup tests
```

## Running Tests

### Prerequisites

```bash
pip install -r requirements_test.txt
```

### Run All Tests

```bash
pytest tests/
```

### Run with Coverage

```bash
pytest tests/ --cov=custom_components/pianobar --cov-report=term-missing
```

### Run Specific Test Files

```bash
pytest tests/test_media_player.py
pytest tests/test_coordinator.py
```

### Run Specific Tests

```bash
pytest tests/test_media_player.py::test_media_player_state_playing
pytest tests/test_config_flow.py::test_form
```

## Test Coverage

### Config Flow Tests (`test_config_flow.py`)

Tests the user configuration flow:
- ✅ Form display and validation
- ✅ Successful connection
- ✅ Connection errors (timeout, cannot connect)
- ✅ Already configured detection
- ✅ Input validation

### Coordinator Tests (`test_coordinator.py`)

Tests the WebSocket coordinator:
- ✅ Connection establishment
- ✅ Connection timeout handling
- ✅ Disconnection cleanup
- ✅ WebSocket reconnection with exponential backoff
- ✅ Event handling for all event types:
  - `process` - Full state updates
  - `start` - Song started
  - `stop` - Playback stopped
  - `progress` - Position updates
  - `volume` - Volume changes
  - `playState` - Pause/resume
  - `stations` - Station list
- ✅ Sending actions and events
- ✅ Message parsing and error handling

### Media Player Tests (`test_media_player.py`)

Tests the media player entity:
- ✅ State management (idle, playing, paused)
- ✅ Volume control:
  - dB to volume level conversion
  - Volume level to percentage conversion
  - Set volume, volume up, volume down
- ✅ Media attributes (title, artist, album, artwork, position, duration)
- ✅ Playback controls (play, pause, next track)
- ✅ Station selection:
  - Source list population
  - Select source by name
  - Play media by station ID
  - Play media by station name
- ✅ Supported features verification
- ✅ Browse media integration

### Browse Media Tests (`test_browse_media.py`)

Tests the media browser functionality:
- ✅ Root level browsing
- ✅ Station list display
- ✅ Empty station list handling
- ✅ Invalid media type handling

### Integration Setup Tests (`test_init.py`)

Tests the integration lifecycle:
- ✅ Setup entry with coordinator
- ✅ Setup failure handling
- ✅ Unload entry cleanup
- ✅ Custom services:
  - `love_song`
  - `ban_song`
  - `tired_of_song`
  - `create_station`
  - `rename_station`
  - `delete_station`

## Test Fixtures (`conftest.py`)

Shared fixtures available to all tests:

- `mock_setup_entry` - Mock integration setup
- `mock_websocket` - Mock WebSocket connection
- `mock_coordinator` - Mock coordinator with default state
- `mock_config_entry` - Mock config entry
- `mock_station_data` - Sample station data
- `mock_song_data` - Sample song data
- `mock_process_event` - Sample process event payload

## CI/CD

Tests run automatically on GitHub Actions for:
- Python 3.11
- Python 3.12

Coverage reports are generated and uploaded to Codecov.

## Writing New Tests

When adding new features, ensure you:

1. **Add tests for the new functionality**
2. **Update fixtures if needed** in `conftest.py`
3. **Maintain test coverage** above 80%
4. **Follow naming conventions**: `test_<feature>_<scenario>`
5. **Use async/await** for async functions
6. **Mock external dependencies** (WebSocket, network calls)

### Example Test

```python
async def test_new_feature(
    hass: HomeAssistant,
    mock_coordinator,
) -> None:
    """Test description."""
    # Arrange
    mock_coordinator.data = {"key": "value"}
    mock_coordinator.some_method = AsyncMock()
    
    # Act
    result = await function_under_test()
    
    # Assert
    assert result == expected_value
    mock_coordinator.some_method.assert_called_once()
```

## Debugging Tests

### Verbose Output

```bash
pytest tests/ -v
```

### Show Print Statements

```bash
pytest tests/ -s
```

### Stop on First Failure

```bash
pytest tests/ -x
```

### Run Only Failed Tests

```bash
pytest tests/ --lf
```

### Debug with pdb

```bash
pytest tests/ --pdb
```

## Mocking Strategy

- **WebSocket connections**: Mocked with `AsyncMock`
- **Network calls**: Mocked with `aiohttp` mocks
- **Home Assistant core**: Uses `pytest-homeassistant-custom-component`
- **Time-dependent code**: Uses `asyncio` test utilities

## Test Isolation

Each test:
- ✅ Runs in isolation
- ✅ Uses fresh mocks
- ✅ Cleans up after itself
- ✅ Doesn't depend on other tests
- ✅ Can run in any order

