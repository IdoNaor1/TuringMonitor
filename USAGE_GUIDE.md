# Turing Smart Screen Monitor - Usage Guide

## 🎉 Your System is Ready!

Your Turing Smart Screen Monitor has been successfully set up and tested. The display protocol has been implemented and verified working with your device (COM3 - USB35INCHIPSV2).

## Quick Start

### Running the Monitor

```bash
# Activate virtual environment (if not already active)
.venv\Scripts\activate

# Run the system monitor
python main.py
```

The monitor will start displaying real-time system stats on your Turing screen:
- Current time
- CPU usage with progress bar
- RAM usage with progress bar

**To stop:** Press `Ctrl+C`

## Available Layouts

Switch between different visual styles by using the `--layout` flag:

### 1. Default Layout (default.json)
Standard 3-widget layout with green CPU bar and blue RAM bar
```bash
python main.py --layout layouts/default.json
```

### 2. Minimal Layout (minimal.json)
Larger time display, CPU only
```bash
python main.py --layout layouts/minimal.json
```

### 3. Compact Layout (compact.json)
Space-efficient with smaller widgets
```bash
python main.py --layout layouts/compact.json
```

### 4. Neon Style (neon.json)
Cyberpunk-inspired with cyan/magenta/green colors on dark background
```bash
python main.py --layout layouts/neon.json
```

### 5. Clean White (clean.json)
Light theme with professional blue/green bars
```bash
python main.py --layout layouts/clean.json
```

## Command-Line Options

```bash
# Specify COM port
python main.py --port COM3

# Use different layout
python main.py --layout layouts/neon.json

# Enable debug mode (verbose output, save images)
python main.py --debug

# Test render without display (creates test_render.png)
python main.py --test-render
```

## Creating Custom Layouts

1. Copy an existing layout from `layouts/` directory
2. Edit the JSON file to customize:
   - `background_color`: Background color in hex (#000000 = black)
   - Widget positions: `{"x": 10, "y": 100}` in pixels
   - Widget sizes: `{"width": 300, "height": 80}` in pixels
   - Colors: All colors use hex format (#RRGGBB)
   - Font sizes: Larger numbers = bigger text

3. Save with a new name in `layouts/` directory
4. Run with: `python main.py --layout layouts/your_layout.json`

### Example Widget Configurations

**Time Display:**
```json
{
  "type": "text",
  "id": "clock",
  "position": {"x": 10, "y": 10},
  "size": {"width": 300, "height": 60},
  "data_source": "time",
  "font_size": 36,
  "color": "#FFFFFF",
  "align": "center"
}
```

**Progress Bar:**
```json
{
  "type": "progress_bar",
  "id": "cpu",
  "position": {"x": 10, "y": 100},
  "size": {"width": 300, "height": 80},
  "data_source": "cpu_percent",
  "label": "CPU",
  "bar_color": "#00FF00",
  "background_color": "#333333",
  "text_color": "#FFFFFF"
}
```

### Available Data Sources

- `time` - Current system time
- `cpu_percent` - CPU usage (0-100)
- `ram_percent` - RAM usage (0-100)
- `ram_used` - RAM used in GB
- `ram_total` - Total RAM in GB

## Configuration

Edit `config.py` to customize:

```python
# Display settings
DISPLAY_WIDTH = 320
DISPLAY_HEIGHT = 480

# Serial settings
COM_PORT = "COM3"  # Your display port
BAUD_RATE = 115200

# Update frequency (milliseconds)
UPDATE_INTERVAL_MS = 1000  # 1 second

# Default layout
DEFAULT_LAYOUT = "layouts/default.json"

# Debug mode
DEBUG = False
SAVE_DEBUG_IMAGES = False
```

## Utilities

### COM Port Scanner
Identify your display's COM port:
```bash
python scanner.py
```

### Test Individual Components
```bash
# Test system monitoring
python monitor.py

# Test widget rendering (creates widget_test.png)
python widgets.py

# Test full rendering (creates render_test.png)
python renderer.py

# Test display connection and protocol
python device_manager.py
```

## Troubleshooting

### Display Not Working
1. Make sure the display is plugged in
2. Run `python scanner.py` to verify COM port
3. Update `COM_PORT` in `config.py` if needed
4. Try running as administrator (Windows)

### Display Shows Wrong Colors
- The display uses RGB565 format - some color precision is lost
- Try adjusting colors in your layout JSON

### Display Updates Slowly
- Reduce `UPDATE_INTERVAL_MS` in config.py for faster updates
- Note: Values below 500ms may cause performance issues

### Connection Errors
- Close any other programs using the COM port
- Unplug and replug the display
- Restart your computer

## Technical Details

### Display Protocol
- **Baud Rate:** 115200
- **Flow Control:** RTS/CTS enabled
- **Pixel Format:** RGB565 (16-bit color)
- **Command Structure:** 6-byte commands with command code in last byte
- **Resolution:** 320x480 pixels (portrait)

### Commands Used
- RESET = 101
- CLEAR = 102
- SCREEN_ON = 109
- SCREEN_OFF = 108
- SET_BRIGHTNESS = 110
- DISPLAY_BITMAP = 197

### Performance
- Full screen update: ~307KB of data (320×480×2 bytes)
- Update frequency: 1 second default (configurable)
- Transfer speed: Limited by 115200 baud serial connection

## Tips & Tricks

1. **Battery Saving:** Lower `UPDATE_INTERVAL_MS` to reduce CPU usage
2. **Custom Metrics:** Edit `monitor.py` to add disk, network, or GPU stats
3. **Startup:** Add `main.py` to Windows startup folder to run automatically
4. **Multiple Displays:** Run multiple instances with different `--port` arguments
5. **Remote Monitoring:** Combine with SSH to monitor remote systems

## Color Reference

### Common Colors (Hex Codes)
- Black: `#000000`
- White: `#FFFFFF`
- Red: `#FF0000`
- Green: `#00FF00`
- Blue: `#0000FF`
- Yellow: `#FFFF00`
- Cyan: `#00FFFF`
- Magenta: `#FF00FF`
- Orange: `#FF8800`
- Purple: `#8800FF`
- Dark Gray: `#333333`
- Light Gray: `#CCCCCC`

## Resources

- **Protocol Research:** `docs/protocol.md`
- **Main Documentation:** `README.md`
- **Hardware Info:** Turing Smart Screen 3.5" (USB35INCHIPSV2)
- **Python Version:** 3.9+ recommended

## Support

For issues or questions:
1. Check `docs/protocol.md` for technical details
2. Review error messages in console output
3. Enable debug mode: `python main.py --debug`
4. Check GitHub issues for similar problems

---

**Enjoy your custom system monitor!** 🚀
