"""Constants for the Crestron Bridge integration."""

DOMAIN = "crestron_bridge"

# Configuration keys
CONF_PORT = "port"

# Defaults
DEFAULT_PORT = 50001

# Fixed entity counts
NUM_LIGHTS = 16
NUM_VIDEO_ENDPOINTS = 4
NUM_AUDIO_ZONES = 4
NUM_VIDEO_SOURCES = 8

# Fixed names
VIDEO_SOURCE_NAMES = [
    "Off",
    "Apple TV",
    "Xbox",
    "PlayStation",
    "Cable Box",
    "Blu-ray",
    "Streaming Device",
    "PC",
]

VIDEO_ENDPOINT_NAMES = [
    "Living Room TV",
    "Bedroom TV",
    "Office TV",
    "Patio TV",
]

AUDIO_ZONE_NAMES = [
    "Living Room",
    "Bedroom",
    "Office",
    "Patio",
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
