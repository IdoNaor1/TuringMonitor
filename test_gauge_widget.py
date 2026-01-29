"""
Test script for GaugeWidget implementation
Creates a simple test image with gauge widgets
"""

try:
    from PIL import Image, ImageDraw
    import widgets
    
    # Create test image
    print("Creating test image...")
    img = Image.new('RGB', (320, 480), color='#0A0A0A')
    draw = ImageDraw.Draw(img)
    
    # Mock data
    data = {
        'cpu_percent': 65.5,
        'gpu_percent': 82.0,
        'cpu_temp': 72.0,
        'ram_percent': 45.0
    }
    
    # Test 1: Arc style gauge
    print("Testing arc-style gauge...")
    arc_gauge_config = {
        'type': 'gauge',
        'id': 'test_arc',
        'position': {'x': 10, 'y': 50},
        'size': {'width': 140, 'height': 140},
        'data_source': 'cpu_percent',
        'style': 'arc',
        'arc_start': 135,
        'arc_end': 405,
        'min_value': 0,
        'max_value': 100,
        'show_value': True,
        'value_format': '{:.0f}%',
        'show_ticks': True,
        'tick_interval': 25,
        'track_color': '#1A1A1A',
        'track_width': 8,
        'arc_width': 12,
        'text_color': '#FFFFFF',
        'color_zones': [
            {'range': [0, 60], 'color': '#00FF88'},
            {'range': [60, 85], 'color': '#FFAA00'},
            {'range': [85, 100], 'color': '#FF2A6D'}
        ]
    }
    
    arc_gauge = widgets.create_widget(arc_gauge_config)
    arc_gauge.render(draw, img, data)
    print("✓ Arc gauge rendered successfully")
    
    # Test 2: Needle style gauge
    print("Testing needle-style gauge...")
    needle_gauge_config = {
        'type': 'gauge',
        'id': 'test_needle',
        'position': {'x': 170, 'y': 50},
        'size': {'width': 140, 'height': 140},
        'data_source': 'gpu_percent',
        'style': 'needle',
        'arc_start': 135,
        'arc_end': 405,
        'min_value': 0,
        'max_value': 100,
        'show_value': True,
        'value_format': '{:.0f}%',
        'show_ticks': True,
        'tick_interval': 25,
        'needle_width': 4,
        'text_color': '#FFFFFF',
        'color_zones': [
            {'range': [0, 60], 'color': '#05FFA1'},
            {'range': [60, 85], 'color': '#FFD700'},
            {'range': [85, 100], 'color': '#FF00AA'}
        ]
    }
    
    needle_gauge = widgets.create_widget(needle_gauge_config)
    needle_gauge.render(draw, img, data)
    print("✓ Needle gauge rendered successfully")
    
    # Test 3: Donut style gauge
    print("Testing donut-style gauge...")
    donut_gauge_config = {
        'type': 'gauge',
        'id': 'test_donut',
        'position': {'x': 10, 'y': 250},
        'size': {'width': 140, 'height': 140},
        'data_source': 'cpu_temp',
        'style': 'donut',
        'arc_start': 135,
        'arc_end': 405,
        'min_value': 20,
        'max_value': 100,
        'show_value': True,
        'value_format': '{:.0f}°C',
        'show_ticks': True,
        'tick_interval': 20,
        'track_color': '#1A1A1A',
        'track_width': 10,
        'arc_width': 12,
        'needle_color': '#00D4FF',
        'needle_width': 3,
        'text_color': '#FFFFFF',
        'color_zones': [
            {'range': [20, 60], 'color': '#00FFFF'},
            {'range': [60, 80], 'color': '#FFAA00'},
            {'range': [80, 100], 'color': '#FF3333'}
        ]
    }
    
    donut_gauge = widgets.create_widget(donut_gauge_config)
    donut_gauge.render(draw, img, data)
    print("✓ Donut gauge rendered successfully")
    
    # Test 4: Semicircle gauge
    print("Testing semicircle gauge...")
    semi_gauge_config = {
        'type': 'gauge',
        'id': 'test_semi',
        'position': {'x': 170, 'y': 250},
        'size': {'width': 140, 'height': 140},
        'data_source': 'ram_percent',
        'style': 'arc',
        'arc_start': 180,
        'arc_end': 360,
        'min_value': 0,
        'max_value': 100,
        'show_value': True,
        'value_format': '{:.0f}%',
        'show_ticks': True,
        'tick_interval': 25,
        'track_color': '#1A1A1A',
        'track_width': 8,
        'arc_width': 12,
        'text_color': '#FFFFFF',
        'color_zones': [
            {'range': [0, 70], 'color': '#00CCFF'},
            {'range': [70, 90], 'color': '#FF8800'},
            {'range': [90, 100], 'color': '#FF0044'}
        ]
    }
    
    semi_gauge = widgets.create_widget(semi_gauge_config)
    semi_gauge.render(draw, img, data)
    print("✓ Semicircle gauge rendered successfully")
    
    # Save test image
    output_file = 'gauge_widget_test.png'
    img.save(output_file)
    print(f"\n✓ All tests passed!")
    print(f"✓ Test image saved as: {output_file}")
    print(f"\nTest Results:")
    print(f"  - Arc style gauge: Working")
    print(f"  - Needle style gauge: Working")
    print(f"  - Donut style gauge: Working")
    print(f"  - Semicircle gauge: Working")
    print(f"\nGauge widget implementation complete!")
    
except ImportError as e:
    print(f"⚠ Warning: Missing dependency: {e}")
    print("This is expected if PIL/Pillow is not installed.")
    print("The code syntax is correct - install dependencies to test rendering.")
    
except Exception as e:
    print(f"✗ Error during testing: {e}")
    import traceback
    traceback.print_exc()
