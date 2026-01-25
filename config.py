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
# Testing shows baud rate doesn't affect speed (hardware limited at ~1.36s)
# Keeping at standard 115200 for compatibility
BAUD_RATE = 115200

# === Update Settings ===
# How often to refresh the display (milliseconds)
UPDATE_INTERVAL_MS = 500

# === Layout Configuration ===
# Path to the layout JSON file
DEFAULT_LAYOUT = "layouts/default.json"

# === Debug Settings ===
# Enable verbose logging
DEBUG = False

# Save rendered images to disk for debugging
SAVE_DEBUG_IMAGES = False
DEBUG_IMAGE_PATH = "debug_output.png"

# === Incremental Rendering Settings ===
# Enable differential updates (only send changed regions)
# This can reduce update time from ~1600ms to ~200ms for typical updates
#
# How it works:
#   - Global: This setting enables/disables the feature entirely
#   - Per-widget: Each widget has an 'update_interval' (in seconds) that controls
#     how often it checks for data changes. This works independently per widget:
#       * time/clock widgets: 1s (update every second)
#       * CPU/GPU metrics: 1s (update every second)
#       * date widgets: 3600s (update every hour)
#       * static images: 3600s (rarely needs updates)
#   - No conflicts: Per-widget intervals only matter when INCREMENTAL_RENDERING=True
#     If disabled, all widgets render every frame regardless of their intervals
INCREMENTAL_RENDERING = True

# Force full render every N seconds to prevent artifacts
# This is a safety mechanism - even with incremental rendering, a full refresh
# happens periodically to ensure the display stays perfectly synchronized
FULL_RENDER_INTERVAL = 300  # 5 minutes

# Log incremental rendering stats (region count, pixel totals)
DEBUG_INCREMENTAL = True
