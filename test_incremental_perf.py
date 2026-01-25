#!/usr/bin/env python3
"""
Test script for incremental rendering performance
Measures render times and compares full vs incremental updates
"""

import time
import sys

# Add project directory to path
sys.path.insert(0, '.')

from renderer import Renderer
from monitor import get_all_metrics


def test_incremental_rendering():
    """Test incremental rendering performance"""
    print("=" * 70)
    print("Incremental Rendering Performance Test")
    print("=" * 70)
    print()

    # Initialize renderer with default layout
    print("Loading renderer with default layout...")
    renderer = Renderer('layouts/default.json')
    print(f"Layout: {renderer.layout.get('name', 'Unknown')}")
    print(f"Widgets: {len(renderer.widget_instances)}")
    print()

    # Get initial metrics
    data = get_all_metrics()

    # Test 1: Full render performance
    print("-" * 70)
    print("Test 1: Full Render Performance")
    print("-" * 70)

    full_times = []
    for i in range(5):
        data = get_all_metrics()
        start = time.time()
        image = renderer.render(data)
        elapsed = (time.time() - start) * 1000
        full_times.append(elapsed)
        print(f"  Full render {i+1}: {elapsed:.1f}ms")

    avg_full = sum(full_times) / len(full_times)
    print(f"  Average: {avg_full:.1f}ms")
    print()

    # Test 2: Incremental render - first call (should be full render)
    print("-" * 70)
    print("Test 2: First Incremental Render (Full)")
    print("-" * 70)

    # Reset renderer caches
    renderer._background_cache = None
    renderer._background_hash = None
    for widget in renderer.widget_instances:
        widget._is_dirty = True

    data = get_all_metrics()
    start = time.time()
    regions = renderer.render_incremental(data, force_full=True)
    elapsed = (time.time() - start) * 1000

    print(f"  Time: {elapsed:.1f}ms")
    print(f"  Regions: {len(regions)}")
    if regions:
        r = regions[0]
        print(f"  Region: ({r['x']}, {r['y']}) {r['width']}x{r['height']}")
    print()

    # Test 3: Incremental render - subsequent calls
    print("-" * 70)
    print("Test 3: Subsequent Incremental Renders")
    print("-" * 70)

    incr_times = []
    incr_regions = []
    incr_pixels = []

    for i in range(20):
        # Small delay to let metrics change
        time.sleep(0.1)
        data = get_all_metrics()

        start = time.time()
        regions = renderer.render_incremental(data, force_full=False)
        elapsed = (time.time() - start) * 1000

        total_pixels = sum(r['width'] * r['height'] for r in regions)

        incr_times.append(elapsed)
        incr_regions.append(len(regions))
        incr_pixels.append(total_pixels)

        print(f"  Update {i+1:2d}: {elapsed:5.1f}ms, {len(regions)} regions, {total_pixels:6d} pixels")

    avg_incr = sum(incr_times) / len(incr_times)
    avg_regions = sum(incr_regions) / len(incr_regions)
    avg_pixels = sum(incr_pixels) / len(incr_pixels)

    print()
    print(f"  Average render time: {avg_incr:.1f}ms")
    print(f"  Average regions: {avg_regions:.1f}")
    print(f"  Average pixels: {avg_pixels:.0f}")
    print()

    # Test 4: Compare full vs incremental
    print("-" * 70)
    print("Test 4: Performance Summary")
    print("-" * 70)

    full_pixels = 320 * 480  # Full frame
    speedup = avg_full / avg_incr if avg_incr > 0 else 0
    pixel_reduction = (1 - avg_pixels / full_pixels) * 100 if full_pixels > 0 else 0

    print(f"  Full render:        {avg_full:.1f}ms ({full_pixels} pixels)")
    print(f"  Incremental render: {avg_incr:.1f}ms ({avg_pixels:.0f} pixels avg)")
    print(f"  Render speedup:     {speedup:.1f}x")
    print(f"  Pixel reduction:    {pixel_reduction:.1f}%")
    print()

    # Estimate communication time savings
    # At ~115200 baud, ~4.4ms per 1000 bytes (2 bytes per pixel in RGB565)
    full_bytes = full_pixels * 2
    incr_bytes = avg_pixels * 2
    full_comm_time = full_bytes / 1000 * 4.4  # Rough estimate
    incr_comm_time = incr_bytes / 1000 * 4.4

    print(f"  Estimated full frame comm time:  {full_comm_time:.0f}ms")
    print(f"  Estimated incremental comm time: {incr_comm_time:.0f}ms")
    print(f"  Estimated total speedup:         {(full_comm_time + avg_full) / (incr_comm_time + avg_incr):.1f}x")
    print()

    print("=" * 70)
    print("Test Complete!")
    print("=" * 70)


def test_widget_dirty_tracking():
    """Test widget dirty tracking functionality"""
    print("=" * 70)
    print("Widget Dirty Tracking Test")
    print("=" * 70)
    print()

    renderer = Renderer('layouts/default.json')

    print(f"Testing {len(renderer.widget_instances)} widgets:")
    print()

    for widget in renderer.widget_instances:
        print(f"Widget: {widget.id}")
        print(f"  Type: {type(widget).__name__}")
        print(f"  Position: ({widget.position['x']}, {widget.position['y']})")
        print(f"  Size: {widget.size['width']}x{widget.size['height']}")
        print(f"  Update interval: {widget.update_interval}s")
        print(f"  Is dirty: {widget._is_dirty}")
        print()

    # Test dirty tracking
    print("-" * 70)
    print("Testing dirty state changes:")
    print("-" * 70)

    data = get_all_metrics()
    current_time = time.time()

    for widget in renderer.widget_instances:
        needs = widget.needs_update(data, current_time)
        print(f"  {widget.id}: needs_update={needs}")
        if needs:
            widget.mark_clean(current_time)

    print()
    print("After marking all clean:")

    # Small delay to allow data to potentially change
    time.sleep(0.5)
    data = get_all_metrics()
    current_time = time.time()

    for widget in renderer.widget_instances:
        needs = widget.needs_update(data, current_time)
        print(f"  {widget.id}: needs_update={needs}")

    print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Test incremental rendering')
    parser.add_argument('--dirty', action='store_true', help='Run dirty tracking test')
    parser.add_argument('--perf', action='store_true', help='Run performance test')

    args = parser.parse_args()

    if args.dirty:
        test_widget_dirty_tracking()
    elif args.perf:
        test_incremental_rendering()
    else:
        # Run both by default
        test_widget_dirty_tracking()
        print("\n" * 2)
        test_incremental_rendering()
