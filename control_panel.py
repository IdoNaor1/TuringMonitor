#!/usr/bin/env python3
"""
Simple Control Panel for Turing Smart Screen Monitor
Interactive menu to control your display
"""

import os
import sys
import time
from device_manager import TuringDisplay
from PIL import Image, ImageDraw, ImageFont

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_menu():
    """Print main menu"""
    clear_screen()
    print("=" * 70)
    print("TURING SMART SCREEN CONTROL PANEL")
    print("=" * 70)
    print()
    print("1. Start System Monitor (Default Layout)")
    print("2. Start System Monitor (Neon Theme)")
    print("3. Start System Monitor (Clean White Theme)")
    print("4. Start System Monitor (Minimal Theme)")
    print("5. Start System Monitor (Compact Theme)")
    print()
    print("6. Display Test Pattern (Red)")
    print("7. Display Test Pattern (Blue)")
    print("8. Display Test Pattern (Green)")
    print("9. Clear Screen (Black)")
    print()
    print("10. Set Brightness (0-100)")
    print("11. Test Connection")
    print("12. Scan COM Ports")
    print()
    print("0. Exit")
    print("=" * 70)

def start_monitor(layout=None):
    """Start the system monitor"""
    clear_screen()
    print("Starting System Monitor...")
    print("Press Ctrl+C to stop")
    print("-" * 70)
    time.sleep(1)

    cmd = ".venv\\Scripts\\python main.py"
    if layout:
        cmd += f" --layout {layout}"

    os.system(cmd)

def display_test_pattern(color):
    """Display a solid color test pattern"""
    clear_screen()
    print(f"Displaying {color} test pattern...")

    display = TuringDisplay()
    if display.connect():
        if color.lower() == 'red':
            img = Image.new('RGB', (320, 480), color=(255, 0, 0))
        elif color.lower() == 'blue':
            img = Image.new('RGB', (320, 480), color=(0, 0, 255))
        elif color.lower() == 'green':
            img = Image.new('RGB', (320, 480), color=(0, 255, 0))

        if display.display_image(img):
            print(f"✓ {color.upper()} pattern displayed!")
            print("Check your display.")
        else:
            print("✗ Failed to display pattern")

        input("\nPress Enter to continue...")
        display.disconnect()
    else:
        print("✗ Failed to connect to display")
        input("\nPress Enter to continue...")

def clear_display():
    """Clear the display (black screen)"""
    clear_screen()
    print("Clearing display...")

    display = TuringDisplay()
    if display.connect():
        if display.clear_screen():
            print("✓ Display cleared!")
        else:
            print("✗ Failed to clear display")

        time.sleep(1)
        display.disconnect()
    else:
        print("✗ Failed to connect to display")

    input("\nPress Enter to continue...")

def set_brightness():
    """Set display brightness"""
    clear_screen()
    print("SET BRIGHTNESS")
    print("-" * 70)

    try:
        level = int(input("Enter brightness level (0-100): "))
        level = max(0, min(100, level))

        display = TuringDisplay()
        if display.connect():
            if display.set_brightness(level):
                print(f"✓ Brightness set to {level}%")
            else:
                print("✗ Failed to set brightness")

            time.sleep(1)
            display.disconnect()
        else:
            print("✗ Failed to connect to display")
    except ValueError:
        print("✗ Invalid input")

    input("\nPress Enter to continue...")

def test_connection():
    """Test connection to display"""
    clear_screen()
    print("TESTING CONNECTION")
    print("-" * 70)

    display = TuringDisplay()
    print("\nAttempting to connect...")

    if display.connect():
        print("✓ Connection successful!")
        print(f"  Port: {display.port}")
        print(f"  Baud Rate: {display.baud_rate}")
        print(f"  Resolution: {display.width}x{display.height}")

        if display.test_connection():
            print("✓ Display is responding")
        else:
            print("✗ Display not responding")

        time.sleep(1)
        display.disconnect()
        print("✓ Disconnected")
    else:
        print("✗ Connection failed")
        print("\nTroubleshooting:")
        print("  1. Make sure display is plugged in")
        print("  2. Check config.py for correct COM port")
        print("  3. Run option 12 to scan for COM ports")

    input("\nPress Enter to continue...")

def scan_ports():
    """Scan for available COM ports"""
    clear_screen()
    os.system(".venv\\Scripts\\python scanner.py")
    input("\nPress Enter to continue...")

def main():
    """Main control panel loop"""
    while True:
        print_menu()

        try:
            choice = input("\nEnter your choice (0-12): ").strip()

            if choice == '0':
                clear_screen()
                print("Goodbye!")
                sys.exit(0)

            elif choice == '1':
                start_monitor()

            elif choice == '2':
                start_monitor("layouts/neon.json")

            elif choice == '3':
                start_monitor("layouts/clean.json")

            elif choice == '4':
                start_monitor("layouts/minimal.json")

            elif choice == '5':
                start_monitor("layouts/compact.json")

            elif choice == '6':
                display_test_pattern('red')

            elif choice == '7':
                display_test_pattern('blue')

            elif choice == '8':
                display_test_pattern('green')

            elif choice == '9':
                clear_display()

            elif choice == '10':
                set_brightness()

            elif choice == '11':
                test_connection()

            elif choice == '12':
                scan_ports()

            else:
                print("\nInvalid choice. Please try again.")
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n\nExiting...")
            sys.exit(0)
        except Exception as e:
            print(f"\nError: {e}")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
