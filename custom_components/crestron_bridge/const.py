"""Constants for the Crestron Bridge integration."""

DOMAIN = "crestron_bridge"

# Configuration keys
CONF_PORT = "port"
CONF_NUM_LIGHTS = "num_lights"
CONF_NUM_VIDEO_ENDPOINTS = "num_video_endpoints"
CONF_NUM_AUDIO_ZONES = "num_audio_zones"
CONF_VIDEO_SOURCE_NAMES = "video_source_names"
CONF_VIDEO_ENDPOINT_NAMES = "video_endpoint_names"
CONF_AUDIO_ZONE_NAMES = "audio_zone_names"

# Defaults
DEFAULT_PORT = 50001
DEFAULT_NUM_LIGHTS = 16
DEFAULT_NUM_VIDEO_ENDPOINTS = 4
DEFAULT_NUM_AUDIO_ZONES = 4
DEFAULT_VIDEO_SOURCES = 8
MAX_LIGHTS = 128

# Default names
DEFAULT_VIDEO_SOURCE_NAMES = [
    "Off",
    "Apple TV",
    "Xbox",
    "PlayStation",
    "Cable Box",
    "Blu-ray",
    "Streaming Device",
    "PC"
]

DEFAULT_VIDEO_ENDPOINT_NAMES = [
    "Living Room TV",
    "Bedroom TV",
    "Office TV",
    "Patio TV"
]

DEFAULT_AUDIO_ZONE_NAMES = [
    "Living Room",
    "Bedroom",
    "Office",
    "Patio"
]

# Protocol constants
KEEPALIVE_INTERVAL = 30
RECONNECT_INTERVAL = 20
MESSAGE_TERMINATOR = "\r\n"

# Volume conversion
CRESTRON_VOLUME_MAX = 65535
HA_VOLUME_MAX = 100

# Protocol commands (TO Crestron)
CMD_LIGHT = "LIGHT"
CMD_QUERY = "QUERY"
CMD_VIDEO = "VIDEO"
CMD_VQUERY = "VQUERY"
CMD_VOLUME = "VOLUME"
CMD_VOLQUERY = "VOLQUERY"
CMD_MUTE = "MUTE"
CMD_MUTEQUERY = "MUTEQUERY"
CMD_KEEPALIVE = "KEEPALIVE"

# Protocol responses (FROM Crestron)
RESP_STATUS = "STATUS"
RESP_VSTATUS = "VSTATUS"
RESP_VOLSTATUS = "VOLSTATUS"
RESP_MUTE = "MUTE"

# Entity types
PLATFORMS = ["switch", "select", "number", "button", "sensor"]
