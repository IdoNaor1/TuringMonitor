"""
Configuration for Turing Smart Screen Monitor
Edit these values to customize your setup
"""

# === Display Configuration ===
DISPLAY_WIDTH = 320
DISPLAY_HEIGHT = 480

# === Serial Communication ===
# Set to "AUTO" for automatic detection (experimental)
# Or specify your COM port: "COM3", "COM5", etc.
COM_PORT = "COM3"

# Baud rate for serial communication
# Common values: 115200, 9600, 57600
# Start with 115200 (most common for these displays)
BAUD_RATE = 115200

# === Update Settings ===
# How often to refresh the display (milliseconds)
UPDATE_INTERVAL_MS = 1000

# === Layout Configuration ===
# Path to the layout JSON file
DEFAULT_LAYOUT = "layouts/default.json"

# === Debug Settings ===
# Enable verbose logging
DEBUG = False

# Save rendered images to disk for debugging
SAVE_DEBUG_IMAGES = False
DEBUG_IMAGE_PATH = "debug_output.png"
