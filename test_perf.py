#!/usr/bin/env python3
"""Performance test script"""
import time
from renderer import Renderer
from monitor import get_all_metrics
from PIL import Image, ImageTk
import tkinter as tk

print("=" * 60)
print("PERFORMANCE TEST")
print("=" * 60)

# Test 1: Raw render
print("\n1. Testing raw render...")
r = Renderer('layouts/minimal.json')
data = get_all_metrics()

start = time.time()
for i in range(10):
    img = r.render(data)
print(f"   10 raw renders: {(time.time()-start)*1000:.0f}ms")

# Test 2: Render + LANCZOS resize
print("\n2. Testing render + LANCZOS resize...")
start = time.time()
for i in range(10):
    img = r.render(data)
    scaled = img.resize((480, 720), Image.Resampling.LANCZOS)
print(f"   10 renders + LANCZOS: {(time.time()-start)*1000:.0f}ms")

# Test 3: Render + faster resize
print("\n3. Testing render + BILINEAR resize...")
start = time.time()
for i in range(10):
    img = r.render(data)
    scaled = img.resize((480, 720), Image.Resampling.BILINEAR)
print(f"   10 renders + BILINEAR: {(time.time()-start)*1000:.0f}ms")

# Test 4: ImageTk.PhotoImage creation
print("\n4. Testing PhotoImage creation...")
root = tk.Tk()
root.withdraw()  # Hide window

start = time.time()
for i in range(10):
    img = r.render(data)
    scaled = img.resize((480, 720), Image.Resampling.LANCZOS)
    photo = ImageTk.PhotoImage(scaled)
print(f"   10 renders + resize + PhotoImage: {(time.time()-start)*1000:.0f}ms")

# Test 5: get_all_metrics timing
print("\n5. Testing get_all_metrics()...")
start = time.time()
for i in range(10):
    data = get_all_metrics()
print(f"   10 get_all_metrics calls: {(time.time()-start)*1000:.0f}ms")

# Test 6: Individual widget creation
print("\n6. Testing widget creation...")
import widgets
widget_config = {
    'type': 'text',
    'id': 'test',
    'position': {'x': 10, 'y': 10},
    'size': {'width': 100, 'height': 30},
    'data_source': 'time',
    'font_size': 24,
    'color': '#FFFFFF'
}

start = time.time()
for i in range(100):
    w = widgets.create_widget(widget_config)
print(f"   100 text widget creations: {(time.time()-start)*1000:.0f}ms")

# Test 7: Full Renderer() creation
print("\n7. Testing Renderer creation...")
start = time.time()
for i in range(10):
    r2 = Renderer('layouts/minimal.json')
print(f"   10 Renderer creations: {(time.time()-start)*1000:.0f}ms")

# Test 8: Renderer with direct layout assignment
print("\n8. Testing Renderer() with manual widget creation...")
import json
with open('layouts/minimal.json') as f:
    layout = json.load(f)

start = time.time()
for i in range(10):
    r3 = Renderer()
    r3.layout = layout
    r3.widget_instances = []
    for wc in layout.get('widgets', []):
        r3.widget_instances.append(widgets.create_widget(wc))
print(f"   10 manual Renderer setups: {(time.time()-start)*1000:.0f}ms")

root.destroy()
print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
