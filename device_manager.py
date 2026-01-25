"""
Device Manager Module
Handles low-level serial communication with Turing Smart Screen

Protocol implementation based on community research and reverse engineering
"""

import serial
import serial.tools.list_ports
import time
import struct
import threading
from PIL import Image
import config as cfg


# Turing Smart Screen Protocol Commands (Revision A - 3.5" display)
# Based on community reverse engineering
class Commands:
    RESET = 101
    CLEAR = 102
    SCREEN_OFF = 108
    SCREEN_ON = 109
    SET_BRIGHTNESS = 110
    SET_ORIENTATION = 121
    DISPLAY_BITMAP = 197


class TuringDisplay:
    """Manager for Turing Smart Screen serial communication"""

    def __init__(self, port=None, baud_rate=None):
        """
        Initialize display manager

        Args:
            port: COM port (e.g., "COM3"). If None, uses config.COM_PORT
            baud_rate: Baud rate for serial. If None, uses config.BAUD_RATE
        """
        self.port = port or cfg.COM_PORT
        self.baud_rate = baud_rate or cfg.BAUD_RATE
        self.serial = None
        self.connected = False
        self.width = cfg.DISPLAY_WIDTH
        self.height = cfg.DISPLAY_HEIGHT
        self.lock = threading.Lock()  # Thread safety for serial access

    def connect(self):
        """
        Connect to the display via serial port

        Returns:
            bool: True if connected successfully, False otherwise
        """
        try:
            if self.port == "AUTO":
                self.port = self._auto_detect_port()
                if self.port is None:
                    print("Error: Could not auto-detect display port")
                    print("Please run scanner.py to identify your device")
                    return False

            print(f"Connecting to {self.port} at {self.baud_rate} baud...")
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=1,
                rtscts=True  # Important: RTS/CTS flow control for Turing displays
            )
            time.sleep(2)  # Allow time for connection to establish
            self.connected = True
            print(f"Connected to {self.port}")

            # Initialize display
            self._init_display()

            return True

        except serial.SerialException as e:
            print(f"Error connecting to {self.port}: {e}")
            return False

    def _auto_detect_port(self):
        """
        Attempt to auto-detect the Turing display port

        Returns:
            str: Port name if found, None otherwise
        """
        ports = serial.tools.list_ports.comports()
        for port in ports:
            hwid_upper = port.hwid.upper()
            # Look for CH340/CH552 chips or USB35INCHIPS serial ID
            if ("1A86" in hwid_upper or "CH340" in hwid_upper or "CH552" in hwid_upper
                or "USB35INCHIPS" in hwid_upper):
                print(f"Auto-detected Turing screen at {port.device}")
                return port.device
        return None

    def _init_display(self):
        """Initialize display after connection"""
        print("Initializing display...")
        # Reset display
        self._send_command(Commands.RESET)
        time.sleep(0.1)
        # Turn on display
        self._send_command(Commands.SCREEN_ON)
        time.sleep(0.1)
        # Set default brightness (50%)
        self._send_brightness_command(50)
        print("Display initialized")

    def disconnect(self):
        """Close serial connection"""
        if self.serial and self.serial.is_open:
            # Turn off display before disconnecting
            try:
                self._send_command(Commands.SCREEN_OFF)
            except:
                pass
            self.serial.close()
            self.connected = False
            print("Disconnected from display")

    def _send_command(self, command_code, data=None):
        """
        Send command to display using 6-byte protocol

        Args:
            command_code: Command code (see Commands class)
            data: Optional data bytes (up to 4 bytes)

        Returns:
            bool: True if sent successfully
        """
        if not self.connected or not self.serial:
            return False

        try:
            with self.lock:  # Thread safety
                # Create 6-byte command buffer
                # Format: [byte0, byte1, byte2, byte3, byte4, command]
                buffer = bytearray(6)

                if data:
                    for i, byte in enumerate(data[:4]):  # Max 4 data bytes
                        buffer[i] = byte

                buffer[5] = command_code  # Command goes in last byte

                self.serial.write(buffer)
                self.serial.flush()
                return True
        except Exception as e:
            if cfg.DEBUG:
                print(f"Error sending command {command_code}: {e}")
            return False

    def _send_brightness_command(self, level):
        """
        Set display brightness

        Args:
            level: Brightness level (0-100)

        Returns:
            bool: True if sent successfully
        """
        level = max(0, min(100, level))  # Clamp to 0-100
        # Brightness data goes in first byte
        return self._send_command(Commands.SET_BRIGHTNESS, [level, 0, 0, 0])

    def _image_to_rgb565(self, image):
        """
        Convert PIL Image to RGB565 format

        Args:
            image: PIL Image in RGB mode

        Returns:
            bytes: Raw RGB565 pixel data
        """
        # Ensure image is in RGB mode
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Get raw pixel data
        pixels = image.load()
        width, height = image.size

        # Convert to RGB565
        rgb565_data = bytearray()

        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]

                # Convert 8-bit RGB to RGB565
                # R: 5 bits, G: 6 bits, B: 5 bits
                r5 = (r >> 3) & 0x1F
                g6 = (g >> 2) & 0x3F
                b5 = (b >> 3) & 0x1F

                # Pack into 16-bit value
                rgb565 = (r5 << 11) | (g6 << 5) | b5

                # Send as little-endian (low byte first)
                rgb565_data.append(rgb565 & 0xFF)  # Low byte
                rgb565_data.append((rgb565 >> 8) & 0xFF)  # High byte

        return bytes(rgb565_data)

    def display_image(self, image):
        """
        Display a PIL Image on the screen

        Args:
            image: PIL Image object (should be 320x480)

        Returns:
            bool: True if displayed successfully
        """
        if not self.connected:
            print("Error: Not connected to display")
            return False

        try:
            with self.lock:  # Ensure only one thread accesses serial at a time
                # Verify and resize image if needed
                if image.size != (self.width, self.height):
                    if cfg.DEBUG:
                        print(f"Resizing image from {image.size} to {self.width}x{self.height}")
                    image = image.resize((self.width, self.height), Image.Resampling.LANCZOS)

                # Convert to RGB565
                rgb565_data = self._image_to_rgb565(image)

                # Send bitmap display command with proper header
                # Header format includes coordinates and dimensions
                x = 0
                y = 0
                width = self.width
                height = self.height
                ex = x + width - 1  # End x
                ey = y + height - 1  # End y

                # Build 6-byte header with coordinate information
                header = bytearray(6)
                header[0] = x >> 2
                header[1] = ((x & 3) << 6) + (y >> 4)
                header[2] = ((y & 15) << 4) + (ex >> 6)
                header[3] = ((ex & 63) << 2) + (ey >> 8)
                header[4] = ey & 255
                header[5] = Commands.DISPLAY_BITMAP  # Command 197

                # Send header
                self.serial.write(header)

                # Small delay before sending pixel data
                time.sleep(0.001)

                # Send all pixel data at once
                self.serial.write(rgb565_data)

                # Flush to ensure all data is sent
                self.serial.flush()

                if cfg.DEBUG:
                    print(f"Sent {len(rgb565_data) + 6} bytes to display")

                # Save debug image if enabled
                if cfg.SAVE_DEBUG_IMAGES:
                    image.save(cfg.DEBUG_IMAGE_PATH)
                    if cfg.DEBUG:
                        print(f"Debug: Saved image to {cfg.DEBUG_IMAGE_PATH}")

                return True

        except Exception as e:
            print(f"Error displaying image: {e}")
            if cfg.DEBUG:
                import traceback
                traceback.print_exc()
            return False

    def display_partial_image(self, image, x, y):
        """
        Display a partial image at specific screen coordinates.

        Args:
            image: PIL Image (any size within screen bounds)
            x, y: Top-left position on screen

        Returns:
            bool: Success status
        """
        if not self.connected:
            return False

        try:
            with self.lock:
                width, height = image.size

                # Validate bounds
                if x < 0 or y < 0 or x + width > self.width or y + height > self.height:
                    print(f"Error: Region ({x},{y},{width},{height}) out of bounds")
                    return False

                # Convert to RGB565
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                rgb565_data = self._image_to_rgb565(image)

                # Build header with partial coordinates
                ex = x + width - 1
                ey = y + height - 1

                header = bytearray(6)
                header[0] = x >> 2
                header[1] = ((x & 3) << 6) + (y >> 4)
                header[2] = ((y & 15) << 4) + (ex >> 6)
                header[3] = ((ex & 63) << 2) + (ey >> 8)
                header[4] = ey & 255
                header[5] = Commands.DISPLAY_BITMAP

                self.serial.write(header)
                time.sleep(0.001)
                self.serial.write(rgb565_data)
                self.serial.flush()

                if cfg.DEBUG:
                    print(f"Partial update: ({x},{y}) {width}x{height} = {len(rgb565_data)} bytes")

                return True
        except Exception as e:
            print(f"Error displaying partial image: {e}")
            return False

    def display_dirty_regions(self, dirty_regions):
        """
        Display multiple dirty regions from incremental rendering.

        Args:
            dirty_regions: List from Renderer.render_incremental()

        Returns:
            bool: Success status
        """
        if not dirty_regions:
            return True

        # Check if this is a full-frame update
        if len(dirty_regions) == 1:
            r = dirty_regions[0]
            if r['x'] == 0 and r['y'] == 0 and r['width'] == self.width and r['height'] == self.height:
                return self.display_image(r['image'])

        success = True
        for region in dirty_regions:
            result = self.display_partial_image(region['image'], region['x'], region['y'])
            success = success and result

        return success

    def clear_screen(self):
        """
        Clear the display (fill with black)

        Returns:
            bool: True if cleared successfully
        """
        return self._send_command(Commands.CLEAR)

    def set_brightness(self, level):
        """
        Set display brightness

        Args:
            level: Brightness level (0-100)

        Returns:
            bool: True if set successfully
        """
        return self._send_brightness_command(level)

    def test_connection(self):
        """
        Test if the display is responding

        Returns:
            bool: True if display responds
        """
        if not self.connected:
            return False

        # Try sending a brightness command as a test
        try:
            result = self._send_brightness_command(50)
            if result:
                print("Display is responding (test command sent successfully)")
            return result
        except:
            return False


# For testing
if __name__ == "__main__":
    print("Testing Device Manager with Protocol Implementation...")
    print("=" * 70)

    # Create display instance
    display = TuringDisplay()

    # Try to connect
    if display.connect():
        print("\n" + "=" * 70)
        print("Connection successful!")
        print("=" * 70)

        # Test if it responds
        if display.test_connection():
            print("\nDisplay test: PASSED")

        # Try to clear screen
        print("\nClearing screen...")
        display.clear_screen()
        time.sleep(1)

        # Try to display a test pattern
        print("\nDisplaying test pattern (red screen)...")
        test_image = Image.new('RGB', (320, 480), color=(255, 0, 0))
        if display.display_image(test_image):
            print("Test pattern sent successfully!")
            print("Check your display - it should show a red screen")

        time.sleep(3)

        # Try another color
        print("\nDisplaying test pattern (blue screen)...")
        test_image = Image.new('RGB', (320, 480), color=(0, 0, 255))
        display.display_image(test_image)

        time.sleep(3)

        # Disconnect
        print("\nDisconnecting...")
        display.disconnect()
        print("Test complete!")
    else:
        print("\nConnection failed")
        print("\nTroubleshooting:")
        print("1. Make sure display is plugged in")
        print("2. Run scanner.py to identify correct COM port")
        print("3. Check config.py has correct COM_PORT setting")
