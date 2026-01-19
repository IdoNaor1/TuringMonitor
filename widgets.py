"""
Widget System for Turing Smart Screen Monitor
Base widget class and built-in widget implementations
"""

from PIL import ImageDraw, ImageFont, Image


def get_component_name_for_data_source(data_source, data):
    """
    Map data source to its component name field
    
    Args:
        data_source: The data source key (e.g., 'cpu_percent', 'gpu_percent')
        data: Dictionary containing all system metrics
        
    Returns:
        str: Component name or None if not available
    """
    # Mapping of data sources to their component name fields
    source_to_name = {
        'cpu_percent': 'cpu_name',
        'cpu_temp': 'cpu_name',
        'cpu_freq_mhz': 'cpu_name',
        'cpu_freq_ghz': 'cpu_name',
        'cpu_core_0': 'cpu_name',
        'cpu_core_1': 'cpu_name',
        'cpu_core_2': 'cpu_name',
        'cpu_core_3': 'cpu_name',
        'cpu_core_4': 'cpu_name',
        'cpu_core_5': 'cpu_name',
        'cpu_core_6': 'cpu_name',
        'cpu_core_7': 'cpu_name',
        'cpu_cores_avg': 'cpu_name',
        'gpu_percent': 'gpu_name',
        'gpu_memory_percent': 'gpu_name',
        'gpu_temp': 'gpu_name',
        'ram_percent': 'ram_name',
        'ram_used': 'ram_name',
        'ram_total': 'ram_name',
        'disk_c_percent': 'disk_name',
        'disk_c_used': 'disk_name',
        'disk_c_total': 'disk_name',
    }
    
    name_field = source_to_name.get(data_source)
    if name_field and name_field in data:
        component_name = data.get(name_field)
        # Filter out generic/unavailable names
        if component_name and component_name not in ['N/A', 'Unknown CPU', '']:
            return component_name
    
    return None


def get_font_filename(family, bold=False, italic=False):
    """
    Map font family and style to Windows font file

    Args:
        family: Font family name (arial, courier, times, consolas, verdana)
        bold: Whether to use bold variant
        italic: Whether to use italic variant

    Returns:
        str: Full path to font file
    """
    fonts = {
        'arial': {
            (False, False): 'arial.ttf',
            (True, False): 'arialbd.ttf',
            (False, True): 'ariali.ttf',
            (True, True): 'arialbi.ttf'
        },
        'courier': {
            (False, False): 'cour.ttf',
            (True, False): 'courbd.ttf',
            (False, True): 'couri.ttf',
            (True, True): 'courbi.ttf'
        },
        'times': {
            (False, False): 'times.ttf',
            (True, False): 'timesbd.ttf',
            (False, True): 'timesi.ttf',
            (True, True): 'timesbi.ttf'
        },
        'consolas': {
            (False, False): 'consola.ttf',
            (True, False): 'consolab.ttf',
            (False, True): 'consolai.ttf',
            (True, True): 'consolaz.ttf'
        },
        'verdana': {
            (False, False): 'verdana.ttf',
            (True, False): 'verdanab.ttf',
            (False, True): 'verdanai.ttf',
            (True, True): 'verdanaz.ttf'
        }
    }

    font_file = fonts.get(family.lower(), {}).get((bold, italic), 'arial.ttf')
    return f"C:\\Windows\\Fonts\\{font_file}"


def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def interpolate_color(color1, color2, factor):
    """
    Interpolate between two colors

    Args:
        color1: Start color (hex string)
        color2: End color (hex string)
        factor: Interpolation factor (0.0 to 1.0)

    Returns:
        str: Interpolated color as hex string
    """
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)

    r = int(rgb1[0] + (rgb2[0] - rgb1[0]) * factor)
    g = int(rgb1[1] + (rgb2[1] - rgb1[1]) * factor)
    b = int(rgb1[2] + (rgb2[2] - rgb1[2]) * factor)

    return f"#{r:02x}{g:02x}{b:02x}"


def draw_rounded_rectangle(draw, bbox, radius, fill):
    """
    Draw rectangle with rounded corners

    Args:
        draw: PIL ImageDraw object
        bbox: Bounding box [x1, y1, x2, y2]
        radius: Corner radius in pixels
        fill: Fill color
    """
    x1, y1, x2, y2 = bbox

    # Draw central rectangle
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)

    # Draw four corner circles
    draw.ellipse([x1, y1, x1 + radius * 2, y1 + radius * 2], fill=fill)
    draw.ellipse([x2 - radius * 2, y1, x2, y1 + radius * 2], fill=fill)
    draw.ellipse([x1, y2 - radius * 2, x1 + radius * 2, y2], fill=fill)
    draw.ellipse([x2 - radius * 2, y2 - radius * 2, x2, y2], fill=fill)


def draw_gradient_rectangle(draw, bbox, start_color, end_color, radius=0, total_width=None):
    """
    Draw rectangle with gradient fill (left to right)

    Args:
        draw: PIL ImageDraw object
        bbox: Bounding box [x1, y1, x2, y2]
        start_color: Start color (hex string)
        end_color: End color (hex string)
        radius: Corner radius (0 for sharp corners)
        total_width: Total width for gradient calculation (if None, uses bbox width)
                     Use this to make gradient scale across full bar width even when partially filled
    """
    x1, y1, x2, y2 = bbox
    width = x2 - x1

    # If total_width is provided, calculate gradient based on that
    # This makes the gradient scale across the full bar, not just the filled portion
    gradient_width = total_width if total_width is not None else width

    # Draw gradient column by column (left to right)
    for i in range(width):
        # Calculate factor based on total gradient width, not just visible width
        factor = i / max(gradient_width - 1, 1)
        color = interpolate_color(start_color, end_color, factor)

        if radius > 0 and (i < radius or i >= width - radius):
            # Handle rounded corners - draw with masking
            # Simplified: just draw the line, proper masking would be more complex
            draw.line([(x1 + i, y1), (x1 + i, y2)], fill=color, width=1)
        else:
            draw.line([(x1 + i, y1), (x1 + i, y2)], fill=color, width=1)


def draw_rounded_rectangle_outline(draw, bbox, radius, color, width):
    """
    Draw outline of rounded rectangle

    Args:
        draw: PIL ImageDraw object
        bbox: Bounding box [x1, y1, x2, y2]
        radius: Corner radius in pixels
        color: Outline color
        width: Line width
    """
    x1, y1, x2, y2 = bbox

    # Draw four lines
    draw.line([(x1 + radius, y1), (x2 - radius, y1)], fill=color, width=width)  # Top
    draw.line([(x1 + radius, y2), (x2 - radius, y2)], fill=color, width=width)  # Bottom
    draw.line([(x1, y1 + radius), (x1, y2 - radius)], fill=color, width=width)  # Left
    draw.line([(x2, y1 + radius), (x2, y2 - radius)], fill=color, width=width)  # Right

    # Draw four corner arcs
    draw.arc([x1, y1, x1 + radius * 2, y1 + radius * 2], 180, 270, fill=color, width=width)
    draw.arc([x2 - radius * 2, y1, x2, y1 + radius * 2], 270, 360, fill=color, width=width)
    draw.arc([x1, y2 - radius * 2, x1 + radius * 2, y2], 90, 180, fill=color, width=width)
    draw.arc([x2 - radius * 2, y2 - radius * 2, x2, y2], 0, 90, fill=color, width=width)


class Widget:
    """Base widget class - all widgets inherit from this"""

    def __init__(self, config):
        """
        Initialize widget with configuration

        Args:
            config: Dictionary containing widget configuration
        """
        self.config = config
        self.id = config.get('id', 'unnamed')
        self.position = config.get('position', {'x': 0, 'y': 0})
        self.size = config.get('size', {'width': 100, 'height': 50})

    def render(self, draw, image, data):
        """
        Render the widget on the image

        Args:
            draw: PIL ImageDraw object
            image: PIL Image object
            data: Dictionary containing system metrics
        """
        raise NotImplementedError("Subclasses must implement render()")


class TextWidget(Widget):
    """Enhanced text display widget with font styling support"""

    def render(self, draw, image, data):
        x = self.position['x']
        y = self.position['y']
        font_size = self.config.get('font_size', 24)
        color = self.config.get('color', '#FFFFFF')
        align = self.config.get('align', 'left')

        # NEW: Font styling
        font_family = self.config.get('font_family', 'arial')
        bold = self.config.get('bold', False)
        italic = self.config.get('italic', False)

        # Get data source
        data_source = self.config.get('data_source', 'time')
        value = data.get(data_source, '')

        # Format temperature values with °C
        if 'temp' in data_source.lower() and isinstance(value, (int, float)):
            text = f"{value:.0f}°C"
        else:
            text = str(value)

        # Load font with styling support
        font = None
        try:
            font_path = get_font_filename(font_family, bold, italic)
            font = ImageFont.truetype(font_path, font_size)
        except:
            # Fallback to simple arial
            try:
                font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", font_size)
            except:
                font = ImageFont.load_default()

        # Calculate text position based on alignment
        if align == 'center':
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            x = x + (self.size['width'] - text_width) // 2
        elif align == 'right':
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            x = x + self.size['width'] - text_width

        draw.text((x, y), text, fill=color, font=font)


class ProgressBarWidget(Widget):
    """Enhanced progress bar widget with gradients, borders, and rounded corners"""

    def render(self, draw, image, data):
        x = self.position['x']
        y = self.position['y']
        width = self.size['width']
        height = self.size['height']

        label = self.config.get('label', '')
        bar_color = self.config.get('bar_color', '#00FF00')
        bg_color = self.config.get('background_color', '#333333')
        text_color = self.config.get('text_color', '#FFFFFF')

        # NEW: Enhanced properties
        border_width = self.config.get('border_width', 0)
        border_color = self.config.get('border_color', '#FFFFFF')
        corner_radius = self.config.get('corner_radius', 0)
        use_gradient = self.config.get('gradient', False)
        gradient_end_color = self.config.get('gradient_end_color', bar_color)
        show_percentage = self.config.get('show_percentage', True)
        show_label = self.config.get('show_label', True)
        display_component_name = self.config.get('display_component_name', False)

        # Get data source value (0-100 percentage)
        data_source = self.config.get('data_source', 'cpu_percent')
        percent = float(data.get(data_source, 0))
        percent = max(0, min(100, percent))  # Clamp to 0-100

        # Try to load fonts
        try:
            font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 18)
            label_font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 14)
            component_name_font = ImageFont.truetype("C:\\Windows\\Fonts\\arialbd.ttf", 11)  # Bold, smaller
        except:
            font = ImageFont.load_default()
            label_font = ImageFont.load_default()
            component_name_font = ImageFont.load_default()

        # Draw label and component name (if enabled)
        label_height = 0
        if label and show_label:
            if display_component_name:
                # Get component name from data
                component_name = get_component_name_for_data_source(data_source, data)
                if component_name:
                    # Draw label on the left
                    draw.text((x, y), label, fill=text_color, font=label_font)
                    # Draw component name on the right (bold, smaller)
                    bbox = draw.textbbox((0, 0), component_name, font=component_name_font)
                    comp_width = bbox[2] - bbox[0]
                    draw.text((x + width - comp_width, y), component_name, fill=text_color, font=component_name_font)
                    label_height = 20
                else:
                    # No component name available, just show label centered
                    draw.text((x, y), label, fill=text_color, font=label_font)
                    label_height = 20
            else:
                # Normal label display
                draw.text((x, y), label, fill=text_color, font=label_font)
                label_height = 20

        # Calculate bar dimensions
        bar_y = y + label_height + 5
        bar_height = height - label_height - 25
        fill_width = int((width * percent) / 100)

        # Draw progress bar background
        if corner_radius > 0:
            draw_rounded_rectangle(draw, [x, bar_y, x + width, bar_y + bar_height], corner_radius, bg_color)
        else:
            draw.rectangle([x, bar_y, x + width, bar_y + bar_height], fill=bg_color)

        # Draw progress bar fill
        if fill_width > 0:
            if use_gradient:
                # Draw gradient fill - scale gradient across full bar width
                draw_gradient_rectangle(draw, [x, bar_y, x + fill_width, bar_y + bar_height],
                                      bar_color, gradient_end_color, corner_radius, total_width=width)
            else:
                # Draw solid fill
                if corner_radius > 0:
                    draw_rounded_rectangle(draw, [x, bar_y, x + fill_width, bar_y + bar_height],
                                         corner_radius, bar_color)
                else:
                    draw.rectangle([x, bar_y, x + fill_width, bar_y + bar_height], fill=bar_color)

        # Draw border if specified
        if border_width > 0:
            if corner_radius > 0:
                draw_rounded_rectangle_outline(draw, [x, bar_y, x + width, bar_y + bar_height],
                                             corner_radius, border_color, border_width)
            else:
                # Draw regular rectangle outline
                for i in range(border_width):
                    draw.rectangle([x + i, bar_y + i, x + width - i, bar_y + bar_height - i],
                                 outline=border_color)

        # Draw percentage text (only if show_percentage is enabled)
        if show_percentage:
            percent_text = f"{percent:.1f}%"
            bbox = draw.textbbox((0, 0), percent_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_x = x + (width - text_width) // 2
            text_y = bar_y + bar_height + 2
            draw.text((text_x, text_y), percent_text, fill=text_color, font=font)


class SparklineWidget(Widget):
    """Mini line graph widget for showing trends over time"""

    def render(self, draw, image, data):
        x = self.position['x']
        y = self.position['y']
        width = self.size['width']
        height = self.size['height']

        # Widget properties
        data_source = self.config.get('data_source', 'cpu_percent')
        label = self.config.get('label', '')
        line_color = self.config.get('line_color', '#00FF00')
        fill_color = self.config.get('fill_color', None)
        bg_color = self.config.get('background_color', '#000000')
        text_color = self.config.get('text_color', '#FFFFFF')
        grid_color = self.config.get('grid_color', '#333333')
        num_points = self.config.get('num_points', 30)
        min_value = self.config.get('min_value', 0)
        max_value = self.config.get('max_value', 100)
        show_current = self.config.get('show_current_value', True)
        display_component_name = self.config.get('display_component_name', False)
        
        # DEBUG LOGGING
        print(f"[SPARKLINE RENDER] label='{label}', line_color={line_color}, "
              f"fill_color={fill_color}, show_current={show_current}")

        # Get historical data
        from monitor import get_data_history
        history = get_data_history(data_source, num_points)

        # Draw background
        draw.rectangle([x, y, x + width, y + height], fill=bg_color)

        # If insufficient data, show placeholder
        if len(history) < 2:
            try:
                font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 12)
            except:
                font = ImageFont.load_default()
            draw.text((x + 5, y + 5), f"{label}: Collecting...",
                     fill=text_color, font=font)
            return

        # Reserve space for label and current value at top
        label_height = 16 if label or show_current or display_component_name else 0
        graph_y = y + label_height
        graph_height = height - label_height - 5  # 5px padding at bottom

        # Reserve space for axis labels (left: min/max values)
        axis_width = 35  # Space for axis labels like "100" or "0"
        graph_x = x + axis_width
        graph_width = width - axis_width - 5  # 5px right padding

        # Load fonts
        try:
            title_font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 12)
            value_font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 10)
            component_name_font = ImageFont.truetype("C:\\Windows\\Fonts\\arialbd.ttf", 11)  # Bold, smaller
            axis_font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 9)
        except:
            title_font = ImageFont.load_default()
            value_font = ImageFont.load_default()
            component_name_font = ImageFont.load_default()
            axis_font = ImageFont.load_default()

        # Draw label and component name in header
        if display_component_name:
            # Get component name from data
            component_name = get_component_name_for_data_source(data_source, data)
            if label and component_name:
                # Draw label on the left
                draw.text((x + 5, y + 2), label, fill=text_color, font=title_font)
                # Draw component name on the right (bold, smaller)
                bbox = draw.textbbox((0, 0), component_name, font=component_name_font)
                comp_width = bbox[2] - bbox[0]
                # Position it considering current value space
                if show_current and len(history) > 0:
                    current = history[-1]
                    current_text = f"{current:.1f}"
                    curr_bbox = draw.textbbox((0, 0), current_text, font=value_font)
                    curr_width = curr_bbox[2] - curr_bbox[0]
                    # Place component name to the left of current value
                    draw.text((x + width - comp_width - curr_width - 10, y + 2), component_name, fill=text_color, font=component_name_font)
                else:
                    # No current value, place at right edge
                    draw.text((x + width - comp_width - 5, y + 2), component_name, fill=text_color, font=component_name_font)
            elif label:
                # Component name not available, just show label
                draw.text((x + 5, y + 2), label, fill=text_color, font=title_font)
        else:
            # Normal label display
            if label:
                draw.text((x + 5, y + 2), label, fill=text_color, font=title_font)

        if show_current and len(history) > 0:
            current = history[-1]
            current_text = f"{current:.1f}"
            bbox = draw.textbbox((0, 0), current_text, font=value_font)
            text_width = bbox[2] - bbox[0]
            draw.text((x + width - text_width - 5, y + 2),
                     current_text, fill=text_color, font=value_font)

        # Draw horizontal grid lines and axis labels
        num_grid_lines = 3  # Min, middle, max
        for i in range(num_grid_lines):
            # Calculate y position for this grid line
            factor = i / (num_grid_lines - 1)
            grid_y_pos = graph_y + graph_height - (factor * graph_height)
            
            # Draw grid line
            draw.line([(graph_x, grid_y_pos), (graph_x + graph_width, grid_y_pos)],
                     fill=grid_color, width=1)
            
            # Draw axis label
            axis_value = min_value + (max_value - min_value) * factor
            axis_text = f"{axis_value:.0f}"
            bbox = draw.textbbox((0, 0), axis_text, font=axis_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            # Position label to the left of the graph, vertically centered on grid line
            draw.text((x + axis_width - text_width - 3, grid_y_pos - text_height // 2),
                     axis_text, fill=text_color, font=axis_font)

        # Calculate point positions for the line graph
        points = []
        x_step = graph_width / max(len(history) - 1, 1)

        for i, value in enumerate(history):
            # Clamp and normalize value
            value_clamped = max(min_value, min(max_value, value))
            value_normalized = (value_clamped - min_value) / max(max_value - min_value, 1)

            point_x = graph_x + i * x_step
            point_y = graph_y + graph_height - (value_normalized * graph_height)
            points.append((point_x, point_y))

        # Draw filled area if fill_color specified
        if fill_color and len(points) >= 2:
            polygon_points = points + [
                (points[-1][0], graph_y + graph_height),
                (points[0][0], graph_y + graph_height)
            ]
            draw.polygon(polygon_points, fill=fill_color)

        # Draw the line graph
        if len(points) >= 2:
            draw.line(points, fill=line_color, width=2)

        # Draw a border around the graph area for clarity
        draw.rectangle([graph_x, graph_y, graph_x + graph_width, graph_y + graph_height],
                      outline=grid_color, width=1)


# Widget factory function
def create_widget(config):
    """
    Create a widget instance from configuration

    Args:
        config: Dictionary containing widget configuration with 'type' field

    Returns:
        Widget instance

    Raises:
        ValueError: If widget type is unknown
    """
    widget_type = config.get('type', 'text')

    if widget_type == 'text':
        return TextWidget(config)
    elif widget_type == 'progress_bar':
        return ProgressBarWidget(config)
    elif widget_type == 'sparkline':
        return SparklineWidget(config)
    else:
        raise ValueError(f"Unknown widget type: {widget_type}")


# For testing
if __name__ == "__main__":
    from PIL import Image
    import monitor

    print("Testing widgets...")

    # Create test image
    img = Image.new('RGB', (320, 480), color='black')
    draw = ImageDraw.Draw(img)

    # Get sample data
    data = monitor.get_all_metrics()

    # Test TextWidget
    text_config = {
        'type': 'text',
        'id': 'test_text',
        'position': {'x': 10, 'y': 10},
        'size': {'width': 300, 'height': 50},
        'data_source': 'time',
        'font_size': 36,
        'color': '#FFFFFF',
        'align': 'center'
    }
    text_widget = create_widget(text_config)
    text_widget.render(draw, img, data)

    # Test ProgressBarWidget
    bar_config = {
        'type': 'progress_bar',
        'id': 'test_bar',
        'position': {'x': 10, 'y': 100},
        'size': {'width': 300, 'height': 80},
        'data_source': 'cpu_percent',
        'label': 'CPU',
        'bar_color': '#00FF00',
        'background_color': '#333333'
    }
    bar_widget = create_widget(bar_config)
    bar_widget.render(draw, img, data)

    # Save test image
    img.save("widget_test.png")
    print("Test image saved as widget_test.png")
