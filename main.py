#!/usr/bin/env python3
"""
Turing Smart Screen Monitor - Main Entry Point
Real-time system monitoring for Turing 3.5" USB displays
"""

import sys
import time
import argparse
from datetime import datetime

import config as cfg
import monitor
import renderer
import device_manager


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Turing Smart Screen Monitor - Display system stats on USB display'
    )
    parser.add_argument(
        '--port',
        type=str,
        help='COM port (e.g., COM3). Overrides config.py'
    )
    parser.add_argument(
        '--layout',
        type=str,
        help='Path to layout JSON file. Overrides config.py'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode (save images to disk)'
    )
    parser.add_argument(
        '--test-render',
        action='store_true',
        help='Test rendering only (no display connection)'
    )

    return parser.parse_args()


def main():
    """Main application loop"""
    args = parse_args()

    print("=" * 70)
    print("Turing Smart Screen Monitor")
    print("=" * 70)
    print()

    # Initialize renderer
    print("Initializing renderer...")
    try:
        layout_path = args.layout if args.layout else cfg.DEFAULT_LAYOUT
        rend = renderer.Renderer(layout_path)
        print(f"Loaded layout: {rend.layout.get('name', 'Unknown')}")
    except Exception as e:
        print(f"Error initializing renderer: {e}")
        return 1

    # Test render mode (no display needed)
    if args.test_render:
        print("\nTest render mode - no display connection")
        print("Rendering test image...")
        data = monitor.get_all_metrics()
        image = rend.render(data)
        image.save("test_render.png")
        print("Test image saved as test_render.png")
        return 0

    # Initialize display
    print("\nInitializing display connection...")
    port = args.port if args.port else None
    display = device_manager.TuringDisplay(port=port)

    if not display.connect():
        print("\nFailed to connect to display")
        print("\nTroubleshooting steps:")
        print("1. Run 'python scanner.py' to identify your display's COM port")
        print("2. Edit config.py and set COM_PORT to your device")
        print("3. Make sure the display is plugged in")
        print("4. Try running as administrator (Windows)")
        return 1

    # Enable debug mode if requested
    if args.debug:
        cfg.DEBUG = True
        cfg.SAVE_DEBUG_IMAGES = True
        print("Debug mode enabled")

    print(f"\nUpdate interval: {cfg.UPDATE_INTERVAL_MS}ms")
    print(f"Incremental rendering: {'Enabled' if cfg.INCREMENTAL_RENDERING else 'Disabled'}")
    print("Press Ctrl+C to stop\n")
    print("-" * 70)

    # Main rendering loop
    frame_count = 0
    last_full_render = 0  # Track last full render for periodic refresh
    try:
        while True:
            loop_start = time.time()

            # Collect system metrics
            data = monitor.get_all_metrics()

            if cfg.INCREMENTAL_RENDERING:
                # Incremental rendering - only update changed regions
                force_full = (time.time() - last_full_render) > cfg.FULL_RENDER_INTERVAL
                dirty_regions = rend.render_incremental(data, force_full=force_full)
                success = display.display_dirty_regions(dirty_regions)

                # Track full render time
                if force_full or (len(dirty_regions) == 1 and dirty_regions[0]['x'] == 0):
                    last_full_render = time.time()

                # Debug logging for incremental mode
                if cfg.DEBUG_INCREMENTAL:
                    total_px = sum(r['width'] * r['height'] for r in dirty_regions)
                    print(f"Incremental: {len(dirty_regions)} regions, {total_px} pixels")
            else:
                # Full frame rendering
                image = rend.render(data)
                success = display.display_image(image)

            # Log progress
            frame_count += 1
            if cfg.DEBUG or frame_count % 10 == 0:
                timestamp = datetime.now().strftime("%H:%M:%S")
                status = "[OK]" if success else "[FAIL]"
                print(f"[{timestamp}] Frame {frame_count}: CPU={data['cpu_percent']:.1f}% RAM={data['ram_percent']:.1f}% {status}")

            # Sleep for remaining time in update interval
            loop_time = (time.time() - loop_start) * 1000  # Convert to ms
            sleep_time = max(0, (cfg.UPDATE_INTERVAL_MS - loop_time) / 1000)
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\n" + "-" * 70)
        print("\nShutting down...")
        display.disconnect()
        print(f"Total frames rendered: {frame_count}")
        print("Goodbye!")
        return 0

    except Exception as e:
        print(f"\nError in main loop: {e}")
        display.disconnect()
        return 1


if __name__ == "__main__":
    sys.exit(main())
