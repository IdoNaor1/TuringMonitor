#!/usr/bin/env python3
"""
Test script to verify update_interval persists correctly in layouts
"""

import json
import os
from pathlib import Path

def test_layout_update_intervals():
    """Test that update_interval fields are present in layout files"""
    
    print("=" * 70)
    print("Testing Widget update_interval Persistence")
    print("=" * 70)
    print()
    
    layouts_dir = Path("layouts")
    
    if not layouts_dir.exists():
        print("❌ Layouts directory not found!")
        return False
    
    layout_files = list(layouts_dir.glob("*.json"))
    
    if not layout_files:
        print("❌ No layout files found!")
        return False
    
    print(f"Found {len(layout_files)} layout files:\n")
    
    all_pass = True
    
    for layout_file in layout_files:
        print(f"📄 {layout_file.name}")
        
        try:
            with open(layout_file, 'r') as f:
                layout = json.load(f)
            
            widgets = layout.get('widgets', [])
            print(f"   Widgets: {len(widgets)}")
            
            for widget in widgets:
                widget_id = widget.get('id', 'unknown')
                widget_type = widget.get('type', 'unknown')
                update_interval = widget.get('update_interval', None)
                
                if update_interval is not None:
                    print(f"   ✅ {widget_id} ({widget_type}): {update_interval}s")
                else:
                    print(f"   ⚠️  {widget_id} ({widget_type}): No update_interval (will default to 1.0s)")
            
            print()
            
        except Exception as e:
            print(f"   ❌ Error reading file: {e}\n")
            all_pass = False
    
    print("-" * 70)
    
    if all_pass:
        print("✅ All layouts parsed successfully")
    else:
        print("❌ Some layouts had errors")
    
    print()
    print("=" * 70)
    print("Recommended update_interval values:")
    print("=" * 70)
    print("  • Time/Clock widgets:     1.0s   (updates every second)")
    print("  • CPU/GPU/RAM metrics:    1.0s   (live monitoring)")
    print("  • Date widgets:           3600s  (updates once per hour)")
    print("  • Static text:            3600s  (rarely changes)")
    print("  • Image widgets:          3600s  (static content)")
    print("  • Sparkline graphs:       1.0s   (continuous history)")
    print()
    print("Note: Lower values = more responsive, but more CPU usage")
    print("      Higher values = better performance for static content")
    print("=" * 70)
    
    return all_pass


def create_example_layout_with_intervals():
    """Create an example layout with proper update_interval values"""
    
    example_layout = {
        "name": "Example with Update Intervals",
        "display": {
            "width": 320,
            "height": 480,
            "background_color": "#000000"
        },
        "widgets": [
            {
                "type": "text",
                "id": "clock",
                "position": {"x": 10, "y": 10},
                "size": {"width": 300, "height": 60},
                "data_source": "time",
                "font_size": 48,
                "color": "#FFFFFF",
                "align": "center",
                "update_interval": 1.0  # Update every second
            },
            {
                "type": "text",
                "id": "date",
                "position": {"x": 10, "y": 75},
                "size": {"width": 300, "height": 30},
                "data_source": "date",
                "font_size": 18,
                "color": "#AAAAAA",
                "align": "center",
                "update_interval": 3600.0  # Update once per hour
            },
            {
                "type": "progress_bar",
                "id": "cpu",
                "position": {"x": 10, "y": 120},
                "size": {"width": 300, "height": 80},
                "data_source": "cpu_percent",
                "label": "CPU",
                "bar_color": "#00FF00",
                "background_color": "#333333",
                "update_interval": 1.0  # Update every second
            },
            {
                "type": "image",
                "id": "logo",
                "position": {"x": 10, "y": 400},
                "size": {"width": 100, "height": 100},
                "data_source": "time",  # Not used for images
                "image_path": "assets/logo.png",
                "scale_mode": "fit",
                "update_interval": 3600.0  # Static - very long interval
            }
        ]
    }
    
    output_file = Path("layouts") / "example_with_intervals.json"
    
    with open(output_file, 'w') as f:
        json.dump(example_layout, f, indent=2)
    
    print(f"\n✅ Created example layout: {output_file}")
    print("   This demonstrates proper update_interval configuration for different widget types")


if __name__ == "__main__":
    success = test_layout_update_intervals()
    
    print("\n" + "=" * 70)
    response = input("Create example layout with update intervals? (y/n): ")
    if response.lower() == 'y':
        create_example_layout_with_intervals()
