"""Constants for the BK Light ACT1026 integration."""

DOMAIN = "bk_light"
CONF_ADDRESS = "address"
CONF_ROTATION = "rotation"
CONF_BRIGHTNESS = "brightness"

DEFAULT_NAME = "BK Light Display"
DEFAULT_BRIGHTNESS = 0.85
DEFAULT_ROTATION = 0

# Device info
MANUFACTURER = "BK Light"
MODEL = "ACT1026"
MODEL_DESCRIPTION = "32x32 RGB LED Matrix"

# BLE UUIDs
UUID_WRITE = "0000fa02-0000-1000-8000-00805f9b34fb"
UUID_NOTIFY = "0000fa03-0000-1000-8000-00805f9b34fb"

# Update interval (seconds)
SCAN_INTERVAL = 30

# Display dimensions
DISPLAY_WIDTH = 32
DISPLAY_HEIGHT = 32

# BLE Protocol constants
HANDSHAKE_FIRST = bytes.fromhex("08 00 01 80 0E 06 32 00")
HANDSHAKE_SECOND = bytes.fromhex("04 00 05 80")
ACK_STAGE_ONE = bytes.fromhex("0C 00 01 80 81 06 32 00 00 01 00 01")
ACK_STAGE_ONE_ALT = bytes.fromhex("0B 00 01 80 83 06 32 00 00 01 00")
ACK_STAGE_TWO = bytes.fromhex("08 00 05 80 0B 03 07 02")
ACK_STAGE_TWO_ALT = bytes.fromhex("08 00 05 80 0E 03 07 01")
ACK_STAGE_THREE = bytes.fromhex("05 00 02 00 03")
