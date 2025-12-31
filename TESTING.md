# Testing Documentation

## Overview

This integration includes a comprehensive test suite with **100+ test cases** covering all aspects of the Pianobar Home Assistant integration.

## Test Statistics

- **5 test modules**
- **60+ individual test cases**
- **Target coverage: >80%**
- **CI/CD: GitHub Actions**
- **Python versions: 3.11, 3.12**

## Quick Start

```bash
# Install dependencies
pip install -r requirements_test.txt

# Run all tests
pytest tests/

# Run with coverage report
pytest tests/ --cov=custom_components/pianobar --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Test Modules

### 1. Config Flow Tests (`test_config_flow.py`)

**Coverage**: User configuration and connection validation

| Test | Description |
|------|-------------|
| `test_form` | User form display and successful setup |
| `test_form_cannot_connect` | Connection error handling |
| `test_form_already_configured` | Duplicate configuration prevention |
| `test_validate_input_success` | Input validation with successful connection |
| `test_validate_input_timeout` | Timeout error handling |

### 2. Coordinator Tests (`test_coordinator.py`)

**Coverage**: WebSocket client and event handling

| Test | Description |
|------|-------------|
| `test_coordinator_connect_success` | Successful WebSocket connection |
| `test_coordinator_connect_timeout` | Connection timeout handling |
| `test_coordinator_disconnect` | Clean disconnection |
| `test_handle_process_event` | Full state update events |
| `test_handle_start_event` | Song start events |
| `test_handle_stop_event` | Playback stop events |
| `test_handle_progress_event` | Position update events |
| `test_handle_volume_event` | Volume change events |
| `test_handle_play_state_event` | Pause/resume events |
| `test_handle_stations_event` | Station list updates |
| `test_send_event` | Sending WebSocket events |
| `test_send_action` | Sending action commands |
| `test_handle_message_parse_event` | Message parsing |
| `test_handle_message_invalid_format` | Invalid message handling |
| `test_handle_message_non_event` | Non-event message filtering |

### 3. Media Player Tests (`test_media_player.py`)

**Coverage**: Media player entity functionality

| Test | Description |
|------|-------------|
| `test_media_player_state_*` | State management (idle/playing/paused) |
| `test_media_player_volume_level` | Volume level conversion |
| `test_media_player_source*` | Station selection |
| `test_media_player_media_attributes` | Media metadata display |
| `test_media_player_play/pause/next` | Playback controls |
| `test_media_player_set_volume` | Volume control |
| `test_media_player_volume_up/down` | Volume stepping |
| `test_media_player_play_media_*` | Play media by ID/name |
| `test_media_player_supported_features` | Feature flags |
| `test_db_to_volume_level_conversions` | dB conversion math |
| `test_volume_level_to_percent` | Percentage conversion |

### 4. Browse Media Tests (`test_browse_media.py`)

**Coverage**: Media browser functionality

| Test | Description |
|------|-------------|
| `test_browse_media_root` | Root level navigation |
| `test_browse_media_stations` | Station list browsing |
| `test_browse_media_empty_stations` | Empty list handling |
| `test_browse_media_invalid_type` | Invalid type handling |

### 5. Integration Tests (`test_init.py`)

**Coverage**: Integration lifecycle and services

| Test | Description |
|------|-------------|
| `test_async_setup_entry` | Integration setup |
| `test_async_setup_entry_connection_error` | Setup failure handling |
| `test_async_unload_entry` | Clean unload |
| `test_service_love_song` | Love song service |
| `test_service_ban_song` | Ban song service |
| `test_service_create_station` | Create station service |
| `test_service_rename_station` | Rename station service |
| `test_service_delete_station` | Delete station service |

## Coverage Goals

| Component | Target | Description |
|-----------|--------|-------------|
| `coordinator.py` | >90% | Critical WebSocket logic |
| `media_player.py` | >90% | Core entity functionality |
| `config_flow.py` | >85% | User configuration |
| `browse_media.py` | >85% | Media browsing |
| `__init__.py` | >80% | Integration setup |

## CI/CD Pipeline

### GitHub Actions Workflow

```yaml
Trigger: Push to main, Pull Requests
Jobs:
  - test (Python 3.11, 3.12)
    - Install dependencies
    - Run pytest with coverage
    - Upload to Codecov
  - lint
    - Run ruff (code quality)
    - Run mypy (type checking)
```

### Status Badges

The README displays:
- ✅ HACS compatibility
- ✅ Latest release version
- ✅ Test status
- ✅ Code coverage percentage

## Testing Best Practices

### 1. Test Isolation

✅ Each test is independent  
✅ Fresh mocks for each test  
✅ No shared state between tests  
✅ Can run in any order  

### 2. Comprehensive Coverage

✅ Happy path scenarios  
✅ Error conditions  
✅ Edge cases  
✅ Invalid inputs  

### 3. Clear Test Structure

```python
async def test_feature(hass, mock_coordinator):
    """Test description."""
    # Arrange - Set up test conditions
    mock_coordinator.data = {...}
    
    # Act - Execute the code under test
    result = await function_under_test()
    
    # Assert - Verify the results
    assert result == expected
```

### 4. Mocking Strategy

✅ Mock external dependencies (WebSocket, network)  
✅ Use AsyncMock for async functions  
✅ Verify calls with assert_called_once()  
✅ Test both success and failure paths  

## Running Specific Test Scenarios

```bash
# Test only config flow
pytest tests/test_config_flow.py

# Test only WebSocket coordinator
pytest tests/test_coordinator.py

# Test volume conversions
pytest tests/test_media_player.py -k volume

# Test with verbose output
pytest tests/ -v

# Stop on first failure
pytest tests/ -x

# Show code coverage in terminal
pytest tests/ --cov=custom_components/pianobar --cov-report=term-missing
```

## Continuous Improvement

When adding new features:

1. ✅ Write tests first (TDD approach)
2. ✅ Ensure tests pass locally
3. ✅ Verify CI passes
4. ✅ Check coverage doesn't decrease
5. ✅ Update test documentation

## Test Maintenance

- **Review tests** when updating dependencies
- **Add tests** for bug fixes (regression tests)
- **Refactor tests** when code changes
- **Update fixtures** when data structures change

## Debugging Failed Tests

```bash
# Run with print statements visible
pytest tests/ -s

# Run with Python debugger
pytest tests/ --pdb

# Re-run only failed tests
pytest tests/ --lf

# Show full diff on assertion failures
pytest tests/ -vv
```

## Future Test Enhancements

Potential additions:
- Integration tests with real WebSocket server
- Performance tests for large station lists
- Stress tests for reconnection logic
- End-to-end tests with Home Assistant instance

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Home Assistant testing](https://developers.home-assistant.io/docs/development_testing/)
- [Test fixtures](./tests/conftest.py)

