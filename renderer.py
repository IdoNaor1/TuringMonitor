"""
Renderer Module
Creates 320x480 dashboard images using Pillow with configurable widget layouts
"""

import json
import os
from PIL import Image, ImageDraw
import widgets
import config as cfg


class Renderer:
    """Image renderer with widget-based layout system"""

    def __init__(self, layout_path=None):
        """
        Initialize renderer with layout configuration

        Args:
            layout_path: Path to layout JSON file (default: from config.py)
        """
        if layout_path is None:
            layout_path = cfg.DEFAULT_LAYOUT

        self.layout = self.load_layout(layout_path)
        self.widget_instances = []

        # Create widget instances from layout
        for widget_config in self.layout.get('widgets', []):
            try:
                widget = widgets.create_widget(widget_config)
                self.widget_instances.append(widget)
            except Exception as e:
                print(f"Warning: Failed to create widget {widget_config.get('id')}: {e}")

        # Display settings
        display_config = self.layout.get('display', {})
        self.width = display_config.get('width', cfg.DISPLAY_WIDTH)
        self.height = display_config.get('height', cfg.DISPLAY_HEIGHT)
        self.bg_color = display_config.get('background_color', '#000000')

    def load_layout(self, layout_path):
        """
        Load layout configuration from JSON file

        Args:
            layout_path: Path to layout JSON file

        Returns:
            dict: Layout configuration

        Raises:
            FileNotFoundError: If layout file doesn't exist
            json.JSONDecodeError: If layout file is invalid JSON
        """
        try:
            with open(layout_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Layout file not found: {layout_path}")
            print("Using default minimal layout")
            return self.get_default_layout()

    def get_default_layout(self):
        """Return a minimal default layout if file not found"""
        return {
            "name": "Emergency Default",
            "display": {
                "width": cfg.DISPLAY_WIDTH,
                "height": cfg.DISPLAY_HEIGHT,
                "background_color": "#000000"
            },
            "widgets": [
                {
                    "type": "text",
                    "id": "time",
                    "position": {"x": 10, "y": 10},
                    "size": {"width": 300, "height": 60},
                    "data_source": "time",
                    "font_size": 36,
                    "color": "#FFFFFF",
                    "align": "center"
                }
            ]
        }

    def render(self, data):
        """
        Render dashboard image with current system data

        Args:
            data: Dictionary containing system metrics from monitor.py

        Returns:
            PIL.Image: Rendered image (320x480 RGB)
        """
        # Check for background image
        display_config = self.layout.get('display', {})
        bg_image_path = display_config.get('background_image', None)

        if bg_image_path:
            # Load background image
            try:
                # Construct full path to background image
                bg_image_full = os.path.join(os.path.dirname(__file__), 'layouts', bg_image_path)
                image = Image.open(bg_image_full)

                # Ensure image is correct size and format
                if image.size != (self.width, self.height):
                    image = image.resize((self.width, self.height), Image.Resampling.LANCZOS)
                image = image.convert('RGB')
            except Exception as e:
                print(f"Warning: Failed to load background image '{bg_image_path}': {e}")
                # Fall back to solid color background
                image = Image.new('RGB', (self.width, self.height), color=self.bg_color)
        else:
            # Solid color background
            image = Image.new('RGB', (self.width, self.height), color=self.bg_color)

        draw = ImageDraw.Draw(image)

        # Render each widget
        for widget in self.widget_instances:
            try:
                widget.render(draw, image, data)
            except Exception as e:
                print(f"Warning: Failed to render widget {widget.id}: {e}")

        return image

    def render_to_bytes(self, data, format='PNG'):
        """
        Render dashboard image and return as bytes

        Args:
            data: Dictionary containing system metrics
            format: Image format (PNG, JPEG, etc.)

        Returns:
            bytes: Image data
        """
        import io
        image = self.render(data)
        buffer = io.BytesIO()
        image.save(buffer, format=format)
        return buffer.getvalue()


# For testing
if __name__ == "__main__":
    import monitor

    print("Testing renderer...")

    # Try to use default layout (may not exist yet)
    try:
        renderer = Renderer()
    except:
        print("Using emergency default layout")
        renderer = Renderer()
        renderer.layout = renderer.get_default_layout()
        renderer.widget_instances = []
        for widget_config in renderer.layout['widgets']:
            renderer.widget_instances.append(widgets.create_widget(widget_config))

    # Get sample data
    data = monitor.get_all_metrics()
    print(f"Rendering with data: CPU={data['cpu_percent']:.1f}%, RAM={data['ram_percent']:.1f}%")

    # Render image
    image = renderer.render(data)

    # Save test image
    image.save("render_test.png")
    print("Test image saved as render_test.png")
