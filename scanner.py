#!/usr/bin/env python3
"""
COM Port Scanner for Turing Smart Screen
Identifies available serial ports to help locate the Turing display
"""

import serial.tools.list_ports


def scan_ports():
    """Scan and display all available COM ports"""
    print("=" * 70)
    print("COM Port Scanner - Turing Smart Screen")
    print("=" * 70)
    print()

    ports = serial.tools.list_ports.comports()

    if not ports:
        print("No COM ports found!")
        print()
        print("Troubleshooting:")
        print("1. Make sure your Turing screen is plugged in")
        print("2. Check if drivers are installed")
        print("3. Try a different USB port")
        return

    print(f"Found {len(ports)} COM port(s):\n")

    for i, port in enumerate(ports, 1):
        print(f"{i}. {port.device}")
        print(f"   Description: {port.description}")
        print(f"   Hardware ID: {port.hwid}")

        # Highlight USB devices
        if "USB" in port.hwid.upper():
            print(f"   >>> This is a USB device (likely candidate)")

        # Check for CH340/CH552 (common Turing screen chips)
        hwid_upper = port.hwid.upper()
        if "CH340" in hwid_upper or "CH552" in hwid_upper or "1A86" in hwid_upper:
            print(f"   >>> ** POSSIBLE TURING SCREEN (CH340/CH552 detected) **")

        print()

    print("=" * 70)
    print("Next Steps:")
    print("1. Identify your Turing screen from the list above")
    print("2. Note the COM port (e.g., COM3, COM5)")
    print("3. Edit config.py and set COM_PORT to your device")
    print("=" * 70)


def main():
    try:
        scan_ports()
    except Exception as e:
        print(f"Error scanning ports: {e}")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())
