"""
Test different baud rates to find the optimal speed
"""
import time
import json
import serial

print("=" * 60)
print("BAUD RATE PERFORMANCE TEST")
print("=" * 60)
print()

# Import modules
from monitor import get_all_metrics
from renderer import Renderer
import config as cfg

# Baud rates to test (from slow to fast)
BAUD_RATES = [115200, 230400, 460800, 921600, 1000000, 1500000, 2000000]

# Load layout
layout_path = r"C:\Users\Ido\AppData\Local\Programs\TuringMonitor\layouts\default.json"
with open(layout_path, 'r') as f:
    layout = json.load(f)

# Create renderer and get test image
renderer = Renderer()
renderer.layout = layout
metrics = get_all_metrics()
image = renderer.render(metrics)

print(f"Testing with {cfg.COM_PORT}")
print(f"Image: {image.size[0]}x{image.size[1]} RGB565")
print(f"Data size: {image.size[0] * image.size[1] * 2 + 6} bytes")
print()
print("=" * 60)

results = []

for baud_rate in BAUD_RATES:
    print(f"\nTesting {baud_rate:,} baud...")
    
    try:
        # Import device manager (reimport to get fresh instance)
        from device_manager import TuringDisplay, Commands
        from PIL import Image as PILImage
        import time as time_module
        
        # Open serial connection directly
        ser = serial.Serial(
            port=cfg.COM_PORT,
            baudrate=baud_rate,
            timeout=2,
            write_timeout=2
        )
        
        # Wait for device to initialize
        time.sleep(0.5)
        
        # Test sending image 3 times
        times = []
        for i in range(3):
            # Convert image to RGB565
            rgb = image.convert('RGB')
            pixels = rgb.load()
            width, height = image.size
            rgb565_data = bytearray(width * height * 2)
            idx = 0
            for y in range(height):
                for x in range(width):
                    r, g, b = pixels[x, y]
                    r5 = (r >> 3) & 0x1F
                    g6 = (g >> 2) & 0x3F
                    b5 = (b >> 3) & 0x1F
                    rgb565 = (r5 << 11) | (g6 << 5) | b5
                    rgb565_data[idx] = (rgb565 >> 8) & 0xFF
                    rgb565_data[idx + 1] = rgb565 & 0xFF
                    idx += 2
            
            # Build header
            x_pos = 0
            y_pos = 0
            ex = x_pos + width - 1
            ey = y_pos + height - 1
            
            header = bytearray(6)
            header[0] = x_pos >> 2
            header[1] = ((x_pos & 3) << 6) + (y_pos >> 4)
            header[2] = ((y_pos & 15) << 4) + (ex >> 6)
            header[3] = ((ex & 63) << 2) + (ey >> 8)
            header[4] = ey & 255
            header[5] = 197  # DISPLAY_BITMAP command
            
            # Time the send operation
            start = time.time()
            ser.write(header)
            time.sleep(0.001)
            ser.write(rgb565_data)
            ser.flush()
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)
            
            print(f"  Attempt {i+1}: {elapsed:.0f}ms")
            time.sleep(0.1)
        
        # Close connection
        ser.close()
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        results.append({
            'baud': baud_rate,
            'avg': avg_time,
            'min': min_time,
            'max': max_time,
            'success': True
        })
        
        print(f"  Average: {avg_time:.0f}ms  (min: {min_time:.0f}ms, max: {max_time:.0f}ms)")
        
    except serial.SerialException as e:
        print(f"  FAILED: {e}")
        results.append({
            'baud': baud_rate,
            'success': False,
            'error': str(e)
        })
    except Exception as e:
        print(f"  ERROR: {e}")
        results.append({
            'baud': baud_rate,
            'success': False,
            'error': str(e)
        })

# Summary
print()
print("=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"{'Baud Rate':>12s}  {'Status':>10s}  {'Avg Time':>10s}  {'Speedup':>10s}")
print("-" * 60)

baseline = None
for result in results:
    if result['success']:
        if baseline is None:
            baseline = result['avg']
        speedup = baseline / result['avg']
        print(f"{result['baud']:>12,}  {'SUCCESS':>10s}  {result['avg']:>9.0f}ms  {speedup:>9.1f}x")
    else:
        print(f"{result['baud']:>12,}  {'FAILED':>10s}  {'N/A':>10s}  {'N/A':>10s}")

# Recommendation
print()
print("=" * 60)
print("RECOMMENDATION")
print("=" * 60)

successful = [r for r in results if r['success']]
if successful:
    best = min(successful, key=lambda x: x['avg'])
    print(f"Best baud rate: {best['baud']:,} ({best['avg']:.0f}ms average)")
    print(f"Speedup from baseline: {baseline / best['avg']:.1f}x")
    print()
    print(f"Update config.py:")
    print(f"  BAUD_RATE = {best['baud']}")
else:
    print("No baud rates worked successfully!")

print()
print("=" * 60)
