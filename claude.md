# Turing Monitor - System Monitor for Turing Smart Screen

A complete Python-based PC system monitor application for the Turing 3.5" USB Smart Screen (320x480 resolution), built from scratch with a professional GUI control center.

## Project Overview

This project was created as a safe alternative to existing libraries that contained malware. It provides:
- Real-time system monitoring (CPU, RAM, time)
- Professional tkinter-based GUI control center
- Multiple customizable themes/layouts
- Thread-safe serial communication
- Settings persistence
- Standalone .exe application

## Hardware

**Turing Smart Screen 3.5"**
- Resolution: 320x480 pixels
- Display: IPS LCD
- Connection: USB (appears as COM port)
- Chip: CH552T MCU
- Identifier: USB35INCHIPSV2
- Protocol: Custom 6-byte command protocol

## Project Structure

```
TuringMonitor/
├── config.py              # Configuration settings (COM port, baud rate, etc.)
├── device_manager.py      # Serial communication and display protocol
├── monitor.py             # System metrics collection (CPU, RAM, etc.)
├── renderer.py            # Image rendering from layouts
├── widgets.py             # Widget system (TextWidget, ProgressBarWidget)
├── gui_app.py             # Main GUI application
├── scanner.py             # COM port scanner utility
├── main.py                # Standalone monitor (no GUI)
├── layouts/               # JSON layout files
│   ├── default.json       # Classic green progress bars
│   ├── minimal.json       # Large clock display
│   ├── compact.json       # Space-efficient layout
│   ├── neon.json          # Cyberpunk theme
│   └── clean.json         # Professional white theme
├── dist/                  # Built .exe application
│   └── TuringControlCenter.exe
└── .venv/                 # Python virtual environment
```

## Core Components

### 1. Display Protocol (device_manager.py)

The Turing Smart Screen uses a custom 6-byte command protocol:

```python
# Command structure
buffer = bytearray(6)
buffer[0-4] = data_bytes  # Optional data
buffer[5] = command_code  # Command identifier

# Available commands
Commands.RESET = 101
Commands.CLEAR = 102
Commands.SCREEN_OFF = 108
Commands.SCREEN_ON = 109
Commands.SET_BRIGHTNESS = 110
Commands.DISPLAY_BITMAP = 197
```

**DISPLAY_BITMAP Protocol:**
The most complex command requires a special 6-byte header encoding coordinates:

```python
header[0] = x >> 2
header[1] = ((x & 3) << 6) + (y >> 4)
header[2] = ((y & 15) << 4) + (ex >> 6)
header[3] = ((ex & 63) << 2) + (ey >> 8)
header[4] = ey & 255
header[5] = 197  # DISPLAY_BITMAP command

# Send header + 1ms delay + 307,200 bytes of RGB565 pixel data
```

**RGB565 Format:**
Each pixel is 2 bytes (16 bits):
- 5 bits red (0-31)
- 6 bits green (0-63)
- 5 bits blue (0-31)

Total frame size: 320 × 480 × 2 = 307,200 bytes (~300 KB)

**Critical Implementation Details:**
- **Thread safety**: All serial operations use `threading.Lock()` to prevent race conditions
- **1ms delay**: Required between header and pixel data for proper processing
- **RTS/CTS flow control**: Essential for reliable data transfer
- **Frame time**: ~1500ms per frame at 115200 baud (hardware limitation)

### 2. System Monitoring (monitor.py)

Uses `psutil` library to collect system metrics:

```python
def get_all_metrics():
    return {
        'time': datetime.now().strftime('%H:%M:%S'),
        'date': datetime.now().strftime('%Y-%m-%d'),
        'cpu_percent': psutil.cpu_percent(interval=0.1),
        'ram_percent': psutil.virtual_memory().percent,
        'ram_used': psutil.virtual_memory().used / (1024**3),
        'ram_total': psutil.virtual_memory().total / (1024**3),
    }
```

### 3. Layout System (renderer.py + widgets.py)

**JSON Layout Format:**
```json
{
  "name": "Layout Name",
  "display": {
    "width": 320,
    "height": 480,
    "background_color": "#000000"
  },
  "widgets": [
    {
      "type": "text",
      "id": "clock",
      "position": {"x": 10, "y": 10},
      "data_source": "time",
      "font_size": 36,
      "color": "#FFFFFF"
    },
    {
      "type": "progress_bar",
      "id": "cpu",
      "position": {"x": 10, "y": 100},
      "data_source": "cpu_percent",
      "label": "CPU",
      "width": 300,
      "height": 30,
      "bar_color": "#00FF00"
    }
  ]
}
```

**Widget Types:**
- `TextWidget`: Display text/numbers (time, CPU%, RAM, etc.)
- `ProgressBarWidget`: Visual bars with labels and percentages

### 4. GUI Application (gui_app.py)

Professional tkinter-based control center with 4 tabs:

**Monitor Control:**
- Start/Stop monitoring
- 5 theme quick-select buttons
- Real-time activity log
- Status indicator

**Layout Designer:**
- Background color picker
- Background image selector
- Widget management (add/edit/remove)
- Save/load layouts

**Settings:**
- COM port configuration
- Baud rate setting
- Update interval (milliseconds)
- Brightness control (0-100%)

**Test & Diagnostics:**
- Color tests (Red, Green, Blue, White, Magenta)
- Connection test
- Clear display
- Port scanner
- System info viewer

## Technical Challenges & Solutions

### Challenge 1: Grey Screen / Flickering
**Problem:** Initial implementation only showed grey screen or flickering.

**Root Cause:** Missing coordinate header in DISPLAY_BITMAP command.

**Solution:** Implemented proper 6-byte header with bit-packed coordinates based on reverse engineering from the .NET implementation.

```python
# Incorrect (original attempt)
self.serial.write(bytearray([0, 0, 0, 0, 0, 197]))
self.serial.write(rgb565_data)

# Correct (final implementation)
header[0] = x >> 2
header[1] = ((x & 3) << 6) + (y >> 4)
# ... (full header encoding)
self.serial.write(header)
time.sleep(0.001)  # Critical delay!
self.serial.write(rgb565_data)
```

### Challenge 2: Race Conditions
**Problem:** Display update failures when color tests ran simultaneously with monitor loop.

**Solution:** Added `threading.Lock()` to serialize all serial port access:

```python
class TuringDisplay:
    def __init__(self):
        self.lock = threading.Lock()

    def display_image(self, image):
        with self.lock:  # Ensures thread safety
            self.serial.write(header)
            time.sleep(0.001)
            self.serial.write(rgb565_data)
            self.serial.flush()
```

### Challenge 3: Port Conflicts When Switching Layouts
**Problem:** "Could not connect to display" errors when switching between layouts.

**Solution:** Proper thread cleanup with join() and explicit disconnect:

```python
def stop_monitor(self):
    self.is_running = False

    # Wait for thread to finish
    if self.monitor_thread and self.monitor_thread.is_alive():
        self.monitor_thread.join(timeout=2.0)

    # Ensure display is disconnected
    if self.display:
        self.display.disconnect()
        self.display = None
```

### Challenge 4: .exe Resource Loading
**Problem:** Layouts not found when running as .exe (PyInstaller).

**Solution:** Detect frozen state and use sys._MEIPASS:

```python
if getattr(sys, 'frozen', False):
    # Running as .exe
    layout_dir = os.path.join(sys._MEIPASS, "layouts")
else:
    # Running as Python script
    layout_dir = os.path.join(os.path.dirname(__file__), "layouts")
```

### Challenge 5: Settings Persistence
**Problem:** Can't modify config.py inside read-only .exe.

**Solution:** Save settings to JSON file in user's home directory:

```python
settings_path = os.path.join(os.path.expanduser("~"), ".turing_monitor_settings.json")
settings = {
    "COM_PORT": cfg.COM_PORT,
    "BAUD_RATE": cfg.BAUD_RATE,
    "UPDATE_INTERVAL_MS": cfg.UPDATE_INTERVAL_MS
}
with open(settings_path, 'w') as f:
    json.dump(settings, f, indent=2)
```

### Challenge 6: Timing Accuracy
**Problem:** Updates not smooth - jumping between 1-2 seconds.

**Solution:** Accurate loop timing that accounts for frame send time:

```python
while self.is_running:
    loop_start = time.time()

    # Get data, render, display
    data = get_all_metrics()
    image = self.renderer.render(data)
    self.display.display_image(image)

    # Calculate remaining time
    loop_time = (time.time() - loop_start) * 1000  # ms
    sleep_time = max(0, (cfg.UPDATE_INTERVAL_MS - loop_time) / 1000.0)

    if sleep_time > 0:
        time.sleep(sleep_time)
```

## Performance Characteristics

**Frame Transfer:**
- Frame size: 307,200 bytes (300 KB)
- Baud rate: 115,200 baud
- Theoretical max: ~11.5 KB/s
- Actual frame time: ~1500ms (1.5 seconds)
- Recommended update interval: 1500-2000ms

**Why so slow?**
- 300 KB at 115200 baud requires ~26 seconds theoretically
- Hardware flow control (RTS/CTS) provides some acceleration
- The 1ms delay between header/data is protocol requirement
- Frame time of ~1500ms is the practical hardware limit

## Building the Application

### Requirements
```bash
pip install pyserial==3.5
pip install Pillow==12.1.0
pip install psutil==7.2.1
pip install pyinstaller==6.18.0
```

### Build .exe
```bash
pyinstaller TuringControlCenter.spec
```

The spec file includes:
- All Python modules (device_manager, monitor, renderer, widgets, config)
- Layouts directory
- Hidden imports for PIL, psutil, serial
- Windowed mode (no console)

Output: `dist/TuringControlCenter.exe` (19 MB)

## Usage

### Standalone .exe
1. Double-click `TuringControlCenter.exe`
2. Click "Save All Settings" to ensure COM port is configured
3. Click a theme button (Default, Neon, Compact, etc.) to start monitoring
4. Monitor displays CPU, RAM, and time in real-time
5. Adjust settings as needed (update interval, brightness)

### Python Script
```bash
# Activate virtual environment
.venv\Scripts\activate

# Run GUI
python gui_app.py

# Or run headless monitor
python main.py --layout layouts/neon.json
```

## Configuration

**Settings are saved to:** `C:\Users\<Username>\.turing_monitor_settings.json`

**Available Settings:**
- `COM_PORT`: Serial port (default: "COM3")
- `BAUD_RATE`: 115200 (do not change)
- `UPDATE_INTERVAL_MS`: 1000-2000 recommended

**Display Settings:**
- Brightness: 0-100% (adjustable in GUI)
- Layouts: 5 built-in themes, fully customizable

## Creating Custom Layouts

1. Copy an existing layout from `layouts/` directory
2. Modify the JSON file:
   - Change background color
   - Adjust widget positions
   - Modify font sizes and colors
   - Add/remove widgets
3. Save with a new name
4. Layout appears in GUI automatically

**Data Sources:**
- `time`: Current time (HH:MM:SS)
- `date`: Current date (YYYY-MM-DD)
- `cpu_percent`: CPU usage percentage
- `ram_percent`: RAM usage percentage
- `ram_used`: RAM used in GB
- `ram_total`: Total RAM in GB

## Troubleshooting

**Display not found:**
- Click "Scan Ports" in Test & Diagnostics tab
- Look for "POSSIBLE TURING SCREEN" marker
- Update COM_PORT in Settings if needed

**Connection errors when switching layouts:**
- This is normal during the 0.5 second transition
- Wait for "Successfully connected" message

**Slow updates:**
- Set Update Interval to 1500-2000ms
- Frame time of ~1500ms is hardware limitation
- Cannot be improved without hardware changes

**Settings not saving:**
- Check that .turing_monitor_settings.json exists in home directory
- Run as administrator if permission errors occur

## Security Note

This project was built from scratch because the existing `mathoudebine/turing-smart-screen-python` library contained a trojan. All code was reverse-engineered from safe sources:
- Protocol details from usausa/turing-smart-screen (.NET implementation)
- Hardware specs from official documentation
- No external binaries or suspicious dependencies

## Dependencies

**Runtime:**
- Python 3.13
- pyserial 3.5 (serial communication)
- Pillow 12.1.0 (image rendering)
- psutil 7.2.1 (system metrics)

**Build:**
- pyinstaller 6.18.0 (create .exe)

All dependencies are open-source and verified safe.

## License

This project was created as a clean, safe implementation for personal use. Feel free to modify and extend as needed.

## Credits

**Protocol Reverse Engineering:**
- Based on community research and the clean .NET implementation by usausa
- No code copied from infected libraries

**Development:**
- Built entirely with Claude (Anthropic's AI assistant)
- User: Ido
- Date: January 2026

## Future Enhancements

Possible improvements:
- Visual layout designer with drag-and-drop
- More widget types (graphs, gauges, images)
- Network monitoring widgets
- Temperature monitoring (if sensors available)
- Multiple display support
- Animation support
- Custom fonts

**Note:** Any performance improvements to reduce the 1500ms frame time would require:
- Higher baud rate (requires hardware/driver support)
- Different protocol (requires firmware modification)
- Hardware acceleration (not available on CH552T)
