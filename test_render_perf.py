"""
Test rendering performance to identify bottlenecks
"""
import time
import json
import os

def measure_time(func, description):
    """Measure execution time of a function"""
    start = time.time()
    result = func()
    elapsed = (time.time() - start) * 1000
    status = "OK"
    if elapsed > 100:
        status = "SLOW!"
    print(f"{description:50s} {elapsed:6.0f}ms  {status}")
    return result, elapsed

print("=" * 60)
print("RENDERING PIPELINE PERFORMANCE TEST")
print("=" * 60)
print()

# Step 1: Import modules
print("Step 1: Importing modules...")
start = time.time()
from monitor import get_all_metrics
from renderer import Renderer
from device_manager import TuringDisplay
import_time = (time.time() - start) * 1000
print(f"  Import time: {import_time:.0f}ms")
print()

# Step 2: Load a layout
print("Step 2: Loading layout...")
layout_path = r"C:\Users\Ido\AppData\Local\Programs\TuringMonitor\layouts\default.json"
if not os.path.exists(layout_path):
    # Try to find any layout
    layouts_dir = r"C:\Users\Ido\AppData\Local\Programs\TuringMonitor\layouts"
    if os.path.exists(layouts_dir):
        files = [f for f in os.listdir(layouts_dir) if f.endswith('.json')]
        if files:
            layout_path = os.path.join(layouts_dir, files[0])

if os.path.exists(layout_path):
    with open(layout_path, 'r') as f:
        layout = json.load(f)
    print(f"  Loaded: {os.path.basename(layout_path)}")
    print(f"  Widgets: {len(layout.get('widgets', []))}")
else:
    print("  ERROR: No layout found!")
    exit(1)
print()

# Step 3: Get metrics
print("Step 3: Getting metrics...")
metrics, metrics_time = measure_time(get_all_metrics, "  get_all_metrics()")
print()

# Step 4: Create renderer (first time)
print("Step 4: Creating renderer (first time)...")
def create_renderer():
    r = Renderer()
    r.layout = layout
    return r

renderer, create_time = measure_time(create_renderer, "  Renderer() + load layout")
print()

# Step 5: First render (creates widget instances)
print("Step 5: First render (creates widgets)...")
def first_render():
    return renderer.render(metrics)

img1, first_render_time = measure_time(first_render, "  renderer.render() #1")
print(f"  Image size: {img1.size}")
print()

# Step 6: Second render (reuses cached widgets)
print("Step 6: Second render (cached widgets)...")
metrics2, metrics_time2 = measure_time(get_all_metrics, "  get_all_metrics() #2")
def second_render():
    return renderer.render(metrics2)

img2, second_render_time = measure_time(second_render, "  renderer.render() #2")
print()

# Step 7: Try to send to device (if available)
print("Step 7: Device communication test...")
try:
    def test_device():
        display = TuringDisplay()
        display.connect()
        display.display_image(img2)
        display.disconnect()
        return True
    
    success, device_time = measure_time(test_device, "  Device connect + send + disconnect")
    if success:
        print("  Device communication successful!")
except Exception as e:
    print(f"  Device not available or error: {e}")
    device_time = 0
print()

# Step 8: Multiple renders to get average
print("Step 8: Running 10 renders to get average...")
times = []
for i in range(10):
    start = time.time()
    m = get_all_metrics()
    img = renderer.render(m)
    elapsed = (time.time() - start) * 1000
    times.append(elapsed)

avg_time = sum(times) / len(times)
min_time = min(times)
max_time = max(times)

print(f"  Average: {avg_time:.0f}ms")
print(f"  Min:     {min_time:.0f}ms")
print(f"  Max:     {max_time:.0f}ms")
print()

# Summary
print("=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Import modules:              {import_time:6.0f}ms")
print(f"Create renderer:             {create_time:6.0f}ms")
print(f"First render (create widgets): {first_render_time:6.0f}ms")
print(f"Second render (cached):      {second_render_time:6.0f}ms")
if device_time > 0:
    print(f"Device communication:        {device_time:6.0f}ms")
print(f"Average render cycle:        {avg_time:6.0f}ms")
print()

# Breakdown analysis
print("BOTTLENECK ANALYSIS:")
print("-" * 60)

if first_render_time > 500:
    print("⚠ First render is slow - widget creation overhead")
if second_render_time > 100:
    print("⚠ Cached renders are slow - rendering logic issue")
if metrics_time > 100:
    print("⚠ get_all_metrics is slow - data collection overhead")
if device_time > 500:
    print("⚠ Device communication is slow - serial port bottleneck")
if avg_time < 200:
    print("✓ Rendering is fast - issue may be elsewhere")
if avg_time > 1000:
    print("✗ Overall performance is poor")
    if device_time > avg_time * 0.5:
        print("  → Device communication is the main bottleneck")
    elif metrics_time > avg_time * 0.3:
        print("  → Metrics collection is a significant factor")
    else:
        print("  → Rendering pipeline needs optimization")

print()
print("=" * 60)
