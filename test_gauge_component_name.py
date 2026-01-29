"""
Test gauge widget with component name display
"""

try:
    from PIL import Image, ImageDraw
    import widgets
    
    # Create test image
    print("Testing gauge with component name display...")
    img = Image.new('RGB', (320, 240), color='#0A0A0A')
    draw = ImageDraw.Draw(img)
    
    # Mock data with component names
    data = {
        'cpu_percent': 65.5,
        'cpu_name': 'Intel i7-9700K',
        'gpu_percent': 82.0,
        'gpu_name': 'NVIDIA RTX 3080',
        'cpu_temp': 72.0,
    }
    
    # Test gauge with component name
    gauge_config = {
        'type': 'gauge',
        'id': 'test_with_name',
        'position': {'x': 10, 'y': 20},
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
        'display_component_name': True,
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
    
    gauge = widgets.create_widget(gauge_config)
    gauge.render(draw, img, data)
    print("✓ Gauge with component name rendered successfully")
    
    # Test GPU gauge with component name
    gauge_config2 = {
        'type': 'gauge',
        'id': 'test_gpu_name',
        'position': {'x': 170, 'y': 20},
        'size': {'width': 140, 'height': 140},
        'data_source': 'gpu_percent',
        'style': 'donut',
        'arc_start': 135,
        'arc_end': 405,
        'min_value': 0,
        'max_value': 100,
        'show_value': True,
        'value_format': '{:.0f}%',
        'show_ticks': False,
        'display_component_name': True,
        'track_color': '#1A1A1A',
        'track_width': 10,
        'arc_width': 12,
        'needle_color': '#00D4FF',
        'needle_width': 3,
        'text_color': '#FFFFFF',
        'color_zones': [
            {'range': [0, 60], 'color': '#00D4FF'},
            {'range': [60, 85], 'color': '#FF8800'},
            {'range': [85, 100], 'color': '#FF00AA'}
        ]
    }
    
    gauge2 = widgets.create_widget(gauge_config2)
    gauge2.render(draw, img, data)
    print("✓ GPU gauge with component name rendered successfully")
    
    # Save test image
    output_file = 'gauge_component_name_test.png'
    img.save(output_file)
    print(f"\n✓ Component name display test passed!")
    print(f"✓ Test image saved as: {output_file}")
    
except ImportError as e:
    print(f"⚠ Warning: Missing dependency: {e}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
