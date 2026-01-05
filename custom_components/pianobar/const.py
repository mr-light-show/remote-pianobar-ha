"""Constants for the Pianobar integration."""

DOMAIN = "pianobar"

# Config flow
CONF_HOST = "host"
CONF_PORT = "port"

DEFAULT_PORT = 8080
DEFAULT_NAME = "Pianobar"

# WebSocket
WS_CONNECT_TIMEOUT = 10
WS_RECONNECT_DELAY = 5
WS_MAX_RECONNECT_DELAY = 300

# Services
SERVICE_LOVE_SONG = "love_song"
SERVICE_BAN_SONG = "ban_song"
SERVICE_TIRED_OF_SONG = "tired_of_song"
SERVICE_CREATE_STATION = "create_station"
SERVICE_RENAME_STATION = "rename_station"
SERVICE_DELETE_STATION = "delete_station"
SERVICE_RECONNECT = "reconnect"
SERVICE_EXPLAIN_SONG = "explain_song"
SERVICE_GET_UPCOMING = "get_upcoming"
SERVICE_SET_QUICK_MIX = "set_quick_mix"
SERVICE_ADD_SEED = "add_seed"
SERVICE_GET_STATION_INFO = "get_station_info"
SERVICE_DELETE_SEED = "delete_seed"
SERVICE_DELETE_FEEDBACK = "delete_feedback"
SERVICE_GET_STATION_MODES = "get_station_modes"
SERVICE_SET_STATION_MODE = "set_station_mode"
SERVICE_TOGGLE_PLAYBACK = "toggle_playback"
SERVICE_RESET_VOLUME = "reset_volume"
SERVICE_SEARCH = "search"
SERVICE_GET_GENRES = "get_genres"
SERVICE_CREATE_STATION_FROM_MUSIC_ID = "create_station_from_music_id"
SERVICE_ADD_SHARED_STATION = "add_shared_station"

# Media browser
MEDIA_TYPE_STATION = "station"

