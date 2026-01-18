# Turing Smart Screen Monitor

A from-scratch Python-based PC system monitor for Turing 3.5-inch USB Smart Screens (320x480 resolution).

## Features

- Real-time system monitoring (CPU, RAM, time)
- Configurable widget-based layout system
- JSON-based layout files for easy customization
- Serial communication with Turing USB displays
- Clean, modular architecture

## Hardware Requirements

- Turing Smart Screen 3.5" (320x480 pixels)
- USB connection (appears as COM port)
- CH552T MCU-based display

## Installation

### 1. Create Virtual Environment

```bash
cd C:\Users\Ido\AppData\Local\Programs\TuringMonitor
python -m venv .venv
```

### 2. Activate Virtual Environment

**Windows:**
```bash
.venv\Scripts\activate
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Step 1: Identify Your Display's COM Port

Run the scanner to find available COM ports:

```bash
python scanner.py
```

Look for your Turing screen in the output. Note the COM port number (e.g., COM3, COM5).

### Step 2: Configure

Edit `config.py` and set your COM port:

```python
COM_PORT = "COM3"  # Replace with your port
```

### Step 3: Run the Monitor

```bash
python main.py
```

Press `Ctrl+C` to stop the monitor.

## Customization

### Layouts

Layouts are defined in JSON files in the `layouts/` directory. The default layout shows:
- Current time (HH:MM:SS)
- CPU usage with progress bar
- RAM usage with progress bar

To create a custom layout:

1. Copy `layouts/default.json` to `layouts/custom.json`
2. Edit the widget configurations (position, size, colors)
3. Run with: `python main.py --layout layouts/custom.json`

### Example Layout Configuration

```json
{
  "name": "My Custom Layout",
  "display": {
    "width": 320,
    "height": 480,
    "background_color": "#000000"
  },
  "update_interval_ms": 1000,
  "widgets": [
    {
      "type": "text",
      "id": "clock",
      "position": {"x": 10, "y": 10},
      "size": {"width": 300, "height": 60},
      "data_source": "time",
      "format": "%H:%M:%S",
      "font_size": 36,
      "color": "#FFFFFF"
    }
  ]
}
```

## Project Structure

```
TuringMonitor/
├── main.py              # Entry point
├── scanner.py           # COM port detection utility
├── config.py            # Configuration
├── device_manager.py    # Serial communication with display
├── monitor.py           # System metrics collection
├── renderer.py          # Image rendering engine
├── widgets.py           # Widget classes
├── layouts/             # Layout configuration files
│   ├── default.json
│   └── minimal.json
└── docs/
    └── protocol.md      # Display protocol notes
```

## Development Status

### Implemented
- ✅ Environment setup
- ✅ COM port scanner
- ✅ System metrics collection (CPU, RAM, time)
- ✅ Widget-based rendering system
- ✅ Configurable JSON layouts

### In Progress
- ⏳ Display protocol implementation (device_manager.py)

### Planned
- ⚪ Additional metrics (disk, network, GPU, temps)
- ⚪ Line graphs and historical data
- ⚪ Custom widgets and plugins

## Troubleshooting

### Display Not Found

- Make sure the Turing screen is plugged in
- Run `scanner.py` to verify it appears as a COM port
- Check Device Manager (Windows) for USB Serial devices

### Permission Errors

- On Linux, add your user to the `dialout` group:
  ```bash
  sudo usermod -a -G dialout $USER
  ```
- Log out and log back in

### Display Shows Nothing

- The protocol implementation is experimental
- Check `docs/protocol.md` for protocol research notes
- Try different baud rates in `config.py`

## Contributing

This is a custom implementation built from scratch. Contributions are welcome, especially for:
- Protocol reverse-engineering
- Additional widget types
- Performance optimizations
- Bug fixes

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Hardware information from CNX Software and Hackaday
- pyserial, Pillow, and psutil library maintainers
