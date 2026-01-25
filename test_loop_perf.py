"""
Test complete monitor loop performance including device communication
"""
import time
import json
import os

print("=" * 60)
print("COMPLETE MONITOR LOOP PERFORMANCE TEST")
print("=" * 60)
print()

# Import modules
print("Importing modules...")
start = time.time()
from monitor import get_all_metrics
from renderer import Renderer
from device_manager import TuringDisplay
import config as cfg
import_time = (time.time() - start) * 1000
print(f"Import time: {import_time:.0f}ms\n")

# Load layout
print("Loading layout...")
layout_path = r"C:\Users\Ido\AppData\Local\Programs\TuringMonitor\layouts\default.json"
if not os.path.exists(layout_path):
    layouts_dir = r"C:\Users\Ido\AppData\Local\Programs\TuringMonitor\layouts"
    if os.path.exists(layouts_dir):
        files = [f for f in os.listdir(layouts_dir) if f.endswith('.json')]
        if files:
            layout_path = os.path.join(layouts_dir, files[0])

with open(layout_path, 'r') as f:
    layout = json.load(f)
print(f"Loaded: {os.path.basename(layout_path)} ({len(layout.get('widgets', []))} widgets)\n")

# Create renderer
renderer = Renderer()
renderer.layout = layout

# Connect to device
print("Connecting to device...")
display = TuringDisplay()
try:
    display.connect()
    print(f"Connected to {cfg.COM_PORT}\n")
    device_connected = True
except Exception as e:
    print(f"Could not connect: {e}")
    print("Running tests without device...\n")
    device_connected = False

# Run timing tests
print("=" * 60)
print("TIMING 10 COMPLETE RENDER CYCLES")
print("=" * 60)
print()

times = {
    'get_metrics': [],
    'render': [],
    'display': [],
    'total': []
}

for i in range(10):
    loop_start = time.time()
    
    # 1. Get metrics
    t1 = time.time()
    metrics = get_all_metrics()
    metrics_time = (time.time() - t1) * 1000
    times['get_metrics'].append(metrics_time)
    
    # 2. Render
    t2 = time.time()
    image = renderer.render(metrics)
    render_time = (time.time() - t2) * 1000
    times['render'].append(render_time)
    
    # 3. Display (if connected)
    t3 = time.time()
    if device_connected:
        display.display_image(image)
    display_time = (time.time() - t3) * 1000
    times['display'].append(display_time)
    
    # Total
    total_time = (time.time() - loop_start) * 1000
    times['total'].append(total_time)
    
    print(f"Cycle {i+1:2d}: Metrics={metrics_time:5.0f}ms  Render={render_time:4.0f}ms  Display={display_time:5.0f}ms  Total={total_time:6.0f}ms")

# Disconnect
if device_connected:
    display.disconnect()

# Calculate statistics
print()
print("=" * 60)
print("STATISTICS (ms)")
print("=" * 60)
print(f"{'Component':<20s} {'Min':>8s} {'Avg':>8s} {'Max':>8s} {'% of Total':>12s}")
print("-" * 60)

total_avg = sum(times['total']) / len(times['total'])

for component in ['get_metrics', 'render', 'display', 'total']:
    values = times[component]
    min_val = min(values)
    avg_val = sum(values) / len(values)
    max_val = max(values)
    pct = (avg_val / total_avg * 100) if component != 'total' and total_avg > 0 else 100.0
    
    print(f"{component:<20s} {min_val:8.0f} {avg_val:8.0f} {max_val:8.0f} {pct:11.1f}%")

print()
print("=" * 60)
print("ANALYSIS")
print("=" * 60)

metrics_pct = (sum(times['get_metrics']) / len(times['get_metrics'])) / total_avg * 100
render_pct = (sum(times['render']) / len(times['render'])) / total_avg * 100
display_pct = (sum(times['display']) / len(times['display'])) / total_avg * 100

if display_pct > 60:
    print(f"⚠ BOTTLENECK: Device communication ({display_pct:.1f}%)")
    print("  The serial port communication is the main bottleneck.")
    print("  This is likely due to:")
    print("  - 115200 baud rate limiting throughput")
    print("  - serial.flush() waiting for all data to be sent")
    print("  - USB-to-serial converter overhead")
    print()
    print("  RECOMMENDATIONS:")
    print("  - Increase baud rate if device supports it (e.g., 921600)")
    print("  - Consider removing serial.flush() if not critical")
    print("  - The 0.5s LHM cache is working as designed")
elif metrics_pct > 40:
    print(f"⚠ BOTTLENECK: Metrics collection ({metrics_pct:.1f}%)")
    print("  Consider increasing LHM cache TTL from 0.5s to 1.0s")
elif render_pct > 30:
    print(f"⚠ BOTTLENECK: Rendering ({render_pct:.1f}%)")
    print("  The PIL rendering might need optimization")
else:
    print(f"✓ Performance is balanced")
    print(f"  Metrics: {metrics_pct:.1f}%")
    print(f"  Render:  {render_pct:.1f}%")
    print(f"  Display: {display_pct:.1f}%")

if total_avg < 500:
    print(f"\n✓ Total cycle time ({total_avg:.0f}ms) is good for {cfg.UPDATE_INTERVAL_MS}ms interval")
elif total_avg < 1000:
    print(f"\n⚠ Total cycle time ({total_avg:.0f}ms) is acceptable but could be better")
else:
    print(f"\n✗ Total cycle time ({total_avg:.0f}ms) is too slow")

print()
print("=" * 60)
