"""
Widget System for Turing Smart Screen Monitor
Base widget class and built-in widget implementations
"""

from PIL import ImageDraw, ImageFont, Image, ImageSequence, ImageOps
import os


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
        'gpu_hotspot_temp': 'gpu_name',
        'gpu_clock': 'gpu_name',
        'gpu_memory_clock': 'gpu_name',
        'gpu_power': 'gpu_name',
        'gpu_memory_used': 'gpu_name',
        'gpu_memory_total': 'gpu_name',
        'ram_percent': 'ram_name',
        'ram_used': 'ram_name',
        'ram_total': 'ram_name',
        'disk_c_percent': 'disk_name',
        'disk_c_used': 'disk_name',
        'disk_c_total': 'disk_name',
        'disk_read_mbs': 'disk_name',
        'disk_write_mbs': 'disk_name',
        'disk_read_kbs': 'disk_name',
        'disk_write_kbs': 'disk_name',
        'dimm_1_temp': 'ram_name',
        'dimm_2_temp': 'ram_name',
        'dimm_3_temp': 'ram_name',
        'dimm_4_temp': 'ram_name',
        'ram_temp_avg': 'ram_name',
        'nvme_temp': 'disk_name',
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


def value_to_angle(value, min_val, max_val, start_angle, end_angle):
    """
    Convert a value to an angle within the gauge's arc range

    Args:
        value: Current value to display
        min_val: Minimum value of gauge range
        max_val: Maximum value of gauge range
        start_angle: Starting angle in degrees
        end_angle: Ending angle in degrees

    Returns:
        float: Angle in degrees
    """
    # Clamp value to range
    value = max(min_val, min(max_val, value))
    
    # Normalize value to 0-1 range
    normalized = (value - min_val) / max(max_val - min_val, 0.0001)
    
    # Map to angle range
    angle_range = end_angle - start_angle
    return start_angle + (normalized * angle_range)


def get_arc_bbox(center_x, center_y, radius):
    """
    Calculate bounding box for an arc given center point and radius

    Args:
        center_x: X coordinate of center
        center_y: Y coordinate of center
        radius: Arc radius

    Returns:
        list: Bounding box [x1, y1, x2, y2]
    """
    return [
        center_x - radius,
        center_y - radius,
        center_x + radius,
        center_y + radius
    ]


def get_needle_endpoint(center_x, center_y, angle, length):
    """
    Calculate endpoint of a needle/pointer at given angle

    Args:
        center_x: X coordinate of pivot point
        center_y: Y coordinate of pivot point
        angle: Angle in degrees (0 = 3 o'clock, 90 = 6 o'clock)
        length: Needle length in pixels

    Returns:
        tuple: (x, y) endpoint coordinates
    """
    import math
    rad = math.radians(angle)
    x = center_x + length * math.cos(rad)
    y = center_y + length * math.sin(rad)
    return (int(x), int(y))


def get_zone_color(value, color_zones):
    """
    Get the color for a value based on color zones

    Args:
        value: Current value
        color_zones: List of zone dicts with 'range' and 'color'
                    e.g., [{'range': [0, 60], 'color': '#00FF00'}, ...]

    Returns:
        str: Hex color string
    """
    for zone in color_zones:
        zone_min, zone_max = zone['range']
        if zone_min <= value <= zone_max:
            return zone['color']
    
    # Default to first zone color if no match
    return color_zones[0]['color'] if color_zones else '#00FF00'


def draw_gauge_arc(draw, center_x, center_y, radius, start_angle, end_angle, color, width):
    """
    Draw an arc segment for gauge visualization

    Args:
        draw: PIL ImageDraw object
        center_x: X coordinate of center
        center_y: Y coordinate of center
        radius: Arc radius
        start_angle: Starting angle in degrees
        end_angle: Ending angle in degrees
        color: Arc color
        width: Arc line width
    """
    bbox = get_arc_bbox(center_x, center_y, radius)
    draw.arc(bbox, start_angle, end_angle, fill=color, width=width)


def draw_gauge_needle(draw, center_x, center_y, angle, length, color, width):
    """
    Draw a needle/pointer for gauge visualization with subtle shadow effect

    Args:
        draw: PIL ImageDraw object
        center_x: X coordinate of pivot point
        center_y: Y coordinate of pivot point
        angle: Angle in degrees
        length: Needle length
        color: Needle color
        width: Needle line width
    """
    end_x, end_y = get_needle_endpoint(center_x, center_y, angle, length)
    
    # Draw subtle shadow (offset by 1-2 pixels)
    shadow_color = '#00000080'  # Semi-transparent black
    shadow_end_x, shadow_end_y = get_needle_endpoint(center_x + 1, center_y + 1, angle, length)
    draw.line([(center_x + 1, center_y + 1), (shadow_end_x, shadow_end_y)], 
              fill=shadow_color, width=width)
    
    # Draw main needle
    draw.line([(center_x, center_y), (end_x, end_y)], fill=color, width=width)
    
    # Draw pivot circle
    pivot_radius = max(3, width)
    draw.ellipse([center_x - pivot_radius, center_y - pivot_radius, 
                  center_x + pivot_radius, center_y + pivot_radius], 
                 fill=color)


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

        # Dirty tracking for incremental rendering
        self._last_data_hash = None
        self._is_dirty = True  # Start dirty - needs initial render
        self._last_update_time = 0
        self.update_interval = config.get('update_interval', 1)  # seconds

    def render(self, draw, image, data):
        """
        Render the widget on the image

        Args:
            draw: PIL ImageDraw object
            image: PIL Image object
            data: Dictionary containing system metrics
        """
        raise NotImplementedError("Subclasses must implement render()")

    def get_relevant_data(self, data):
        """
        Extract only the data this widget depends on.
        Override in subclasses for more specific data extraction.

        Args:
            data: Full metrics dictionary

        Returns:
            The relevant data value(s) for this widget
        """
        data_source = self.config.get('data_source')
        return data.get(data_source) if data_source else None

    def needs_update(self, data, current_time):
        """
        Check if widget needs re-rendering.

        Args:
            data: Current metrics data
            current_time: Current time.time() value

        Returns:
            bool: True if widget should be re-rendered
        """
        # Force update if never rendered
        if self._is_dirty:
            return True

        # Check time-based update interval
        if current_time - self._last_update_time < self.update_interval:
            return False

        # Check if data changed
        relevant_data = self.get_relevant_data(data)
        data_hash = hash(str(relevant_data))

        if data_hash != self._last_data_hash:
            self._last_data_hash = data_hash
            return True

        return False

    def mark_clean(self, current_time):
        """Mark widget as up-to-date after rendering."""
        self._is_dirty = False
        self._last_update_time = current_time

    def mark_dirty(self):
        """Force widget to re-render on next update."""
        self._is_dirty = True

    def render_to_image(self, data):
        """
        Render widget to its own PIL Image for incremental rendering.

        Args:
            data: Metrics data dictionary

        Returns:
            PIL.Image: Widget rendered to RGBA image
        """
        w = self.size['width']
        h = self.size['height']
        widget_img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(widget_img)

        # Temporarily shift position to origin for relative drawing
        original_pos = self.position.copy()
        self.position = {'x': 0, 'y': 0}
        self.render(draw, widget_img, data)
        self.position = original_pos

        return widget_img


class TextWidget(Widget):
    """Enhanced text display widget with font styling support"""

    def get_relevant_data(self, data):
        """TextWidget depends on its data_source value."""
        data_source = self.config.get('data_source', 'time')
        return data.get(data_source)

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
        # Format disk data with GB and 2 decimal places
        elif data_source in ['disk_c_used', 'disk_c_total'] and isinstance(value, (int, float)):
            text = f"{value:.2f} GB"
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

    def get_relevant_data(self, data):
        """ProgressBarWidget depends on its data_source percentage value."""
        data_source = self.config.get('data_source', 'cpu_percent')
        return data.get(data_source)

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

    def get_relevant_data(self, data):
        """SparklineWidget depends on historical data, which changes every frame."""
        data_source = self.config.get('data_source', 'cpu_percent')
        num_points = self.config.get('num_points', 30)
        from monitor import get_data_history
        # Return tuple of history for hashing
        return tuple(get_data_history(data_source, num_points))

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


class GaugeWidget(Widget):
    """Circular/radial gauge widget for percentage/value display with multiple styles"""

    def get_relevant_data(self, data):
        """GaugeWidget depends on its data_source value."""
        data_source = self.config.get('data_source', 'cpu_percent')
        return data.get(data_source)

    def render(self, draw, image, data):
        import math
        
        # Extract position and size
        x = self.position['x']
        y = self.position['y']
        width = self.size['width']
        height = self.size['height']
        
        # Get configuration
        style = self.config.get('style', 'arc')  # 'arc', 'needle', 'donut'
        arc_start = self.config.get('arc_start', 135)  # degrees
        arc_end = self.config.get('arc_end', 405)  # degrees (can exceed 360)
        
        # Color zones: list of {'range': [min, max], 'color': '#RRGGBB'}
        color_zones = self.config.get('color_zones', [
            {'range': [0, 100], 'color': '#00FF00'}
        ])
        
        # Display options
        show_value = self.config.get('show_value', True)
        value_format = self.config.get('value_format', '{:.1f}%')
        show_ticks = self.config.get('show_ticks', True)
        tick_interval = self.config.get('tick_interval', 25)  # Show tick every 25%
        
        # Styling
        track_color = self.config.get('track_color', '#333333')
        track_width = self.config.get('track_width', 8)
        arc_width = self.config.get('arc_width', 10)
        needle_color = self.config.get('needle_color', '#FF2A6D')
        needle_width = self.config.get('needle_width', 3)
        text_color = self.config.get('text_color', '#FFFFFF')
        
        # Get data value
        data_source = self.config.get('data_source', 'cpu_percent')
        value = float(data.get(data_source, 0))
        min_val = self.config.get('min_value', 0)
        max_val = self.config.get('max_value', 100)
        
        # Clamp value to range
        value = max(min_val, min(max_val, value))
        
        # Calculate center and radius
        center_x = x + width // 2
        center_y = y + height // 2
        radius = min(width, height) // 2 - 15  # padding for labels
        
        # Calculate value angle
        value_angle = value_to_angle(value, min_val, max_val, arc_start, arc_end)
        
        # Draw background track
        if style in ['arc', 'donut']:
            draw_gauge_arc(draw, center_x, center_y, radius, arc_start, arc_end, 
                          track_color, track_width)
        
        # Draw color zone arcs (discrete segments)
        if style in ['arc', 'donut']:
            for zone in color_zones:
                zone_min, zone_max = zone['range']
                zone_color = zone['color']
                
                # Calculate angles for this zone
                zone_start_angle = value_to_angle(zone_min, min_val, max_val, arc_start, arc_end)
                zone_end_angle = value_to_angle(zone_max, min_val, max_val, arc_start, arc_end)
                
                # Only draw the portion that's filled (up to value_angle)
                if value_angle >= zone_start_angle:
                    actual_end = min(value_angle, zone_end_angle)
                    draw_gauge_arc(draw, center_x, center_y, radius, 
                                  zone_start_angle, actual_end, zone_color, arc_width)
        
        # Draw needle (for needle or donut+needle hybrid styles)
        if style in ['needle', 'donut']:
            # Needle extends from center
            needle_length = radius - 5
            current_color = get_zone_color(value, color_zones)
            draw_gauge_needle(draw, center_x, center_y, value_angle, needle_length, 
                            current_color if style == 'needle' else needle_color, needle_width)
        
        # Draw center circle for donut style
        if style == 'donut':
            inner_radius = radius - arc_width - 5
            inner_bbox = get_arc_bbox(center_x, center_y, inner_radius)
            draw.ellipse(inner_bbox, fill='#000000', outline=track_color, width=2)
        
        # Draw tick marks
        if show_ticks and tick_interval > 0:
            tick_font = None
            try:
                tick_font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 10)
            except:
                tick_font = ImageFont.load_default()
            
            # Calculate tick positions
            value_range = max_val - min_val
            num_ticks = int(value_range / tick_interval) + 1
            
            for i in range(num_ticks):
                tick_value = min_val + (i * tick_interval)
                if tick_value > max_val:
                    break
                    
                tick_angle = value_to_angle(tick_value, min_val, max_val, arc_start, arc_end)
                
                # Draw tick mark (small line)
                tick_start = radius - arc_width - 3
                tick_end = radius - arc_width - 8
                tick_start_pos = get_needle_endpoint(center_x, center_y, tick_angle, tick_start)
                tick_end_pos = get_needle_endpoint(center_x, center_y, tick_angle, tick_end)
                draw.line([tick_start_pos, tick_end_pos], fill='#888888', width=2)
                
                # Draw tick label
                label_distance = radius - arc_width - 18
                label_pos = get_needle_endpoint(center_x, center_y, tick_angle, label_distance)
                tick_text = f"{int(tick_value)}"
                
                # Calculate text bounds for centering
                bbox = draw.textbbox((0, 0), tick_text, font=tick_font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                label_x = label_pos[0] - text_width // 2
                label_y = label_pos[1] - text_height // 2
                draw.text((label_x, label_y), tick_text, fill='#888888', font=tick_font)
        
        # Draw center value text
        if show_value:
            try:
                value_font = ImageFont.truetype("C:\\Windows\\Fonts\\arialbd.ttf", 20)
            except:
                value_font = ImageFont.load_default()
            
            # Format value text
            if isinstance(value_format, str):
                value_text = value_format.format(value)
            else:
                value_text = f"{value:.1f}%"
            
            # Calculate text position (centered)
            bbox = draw.textbbox((0, 0), value_text, font=value_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            text_x = center_x - text_width // 2
            text_y = center_y - text_height // 2
            
            # For donut style, position text in center
            # For arc/needle, position below center
            if style == 'donut':
                text_y = center_y - text_height // 2
            else:
                text_y = center_y + radius // 3
            
            draw.text((text_x, text_y), value_text, fill=text_color, font=value_font)
        
        # Draw component name if enabled
        display_component_name = self.config.get('display_component_name', False)
        if display_component_name:
            component_name = get_component_name_for_data_source(data_source, data)
            if component_name:
                try:
                    component_font = ImageFont.truetype("C:\\Windows\\Fonts\\arialbd.ttf", 10)
                except:
                    component_font = ImageFont.load_default()
                
                # Position component name below the gauge
                comp_bbox = draw.textbbox((0, 0), component_name, font=component_font)
                comp_width = comp_bbox[2] - comp_bbox[0]
                comp_x = center_x - comp_width // 2
                comp_y = y + height - 15
                
                draw.text((comp_x, comp_y), component_name, fill='#888888', font=component_font)


class ImageWidget(Widget):
    """
    Widget for displaying images
    """
    def __init__(self, config):
        sys_config = config.copy()
        # Ensure size is set, default to 100x100 if not provided
        if 'size' not in sys_config:
            sys_config['size'] = {'width': 100, 'height': 100}
            
        super().__init__(sys_config)
        
        self.image_path = config.get('image_path', '')
        self.scale_mode = config.get('scale_mode', 'fit') # fit, fill, stretch, center
        self.opacity = config.get('opacity', 1.0) # 0.0 to 1.0
        self.rotation = config.get('rotation', 0) # 0, 90, 180, 270
        
        self.image = None
        self.processed_image = None  # Cache the processed image
        self.render_position = None   # Cache the render position
        self._load_image()

    def needs_update(self, data, current_time):
        """ImageWidget only renders once (static content)."""
        if self._is_dirty:
            self._is_dirty = False
            self._last_update_time = current_time
            return True
        return False

    def _load_image(self):
        """Load and pre-process image from disk"""
        if not self.image_path:
            return
            
        # Try to find the image file
        # Check absolute path first
        full_path = self.image_path
        if not os.path.exists(full_path):
            # Check relative to layouts directory
            import config as cfg
            full_path = os.path.join(os.path.dirname(__file__), 'layouts', self.image_path)
            
        if not os.path.exists(full_path):
            # Check relative to assets directory if it existed, but let's just try relative to cwd
            full_path = os.path.abspath(self.image_path)
            
        if os.path.exists(full_path):
            try:
                img = Image.open(full_path)
                self.image = img.convert('RGBA')
                # Pre-process the image once
                self._process_image()
            except Exception as e:
                print(f"[ImageWidget] Error loading image {full_path}: {e}")
        else:
            print(f"[ImageWidget] Image not found: {self.image_path}")
            
    def _process_image(self):
        """Pre-process the image (rotation, scaling, opacity) - called once"""
        if not self.image:
            return
            
        current_img = self.image
            
        # Rotate if needed
        if self.rotation != 0:
            current_img = current_img.rotate(-self.rotation, expand=True)

        # Target size
        target_w = self.size['width']
        target_h = self.size['height']
        
        # Scale image according to mode
        img_w, img_h = current_img.size
        
        final_img = None
        
        if self.scale_mode == 'stretch':
            final_img = current_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            
        elif self.scale_mode == 'fit':
            # Maintain aspect ratio, fit inside
            ratio = min(target_w / img_w, target_h / img_h)
            new_w = int(img_w * ratio)
            new_h = int(img_h * ratio)
            final_img = current_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
        elif self.scale_mode == 'fill':
            # Maintain aspect ratio, cover area (crop)
            ratio = max(target_w / img_w, target_h / img_h)
            new_w = int(img_w * ratio)
            new_h = int(img_h * ratio)
            resized = current_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            # Center crop
            left = (new_w - target_w) // 2
            top = (new_h - target_h) // 2
            final_img = resized.crop((left, top, left + target_w, top + target_h))
            
        elif self.scale_mode == 'center':
            # No scaling, just center
            final_img = current_img
            
        # Apply opacity if needed
        if self.opacity < 1.0:
            # Process alpha channel
            final_img.putalpha(Image.eval(final_img.getchannel('A'), lambda x: int(x * self.opacity)))
            
        # Cache the processed image
        self.processed_image = final_img
        
        # Calculate and cache the render position
        fw, fh = final_img.size
        x_offset = self.position['x'] + (target_w - fw) // 2
        y_offset = self.position['y'] + (target_h - fh) // 2
        self.render_position = (x_offset, y_offset)
            
    def render(self, draw, image, data):
        """Render the pre-processed image - very fast, just paste"""
        if not self.processed_image:
            return
        
        # Simply paste the pre-processed image
        image.paste(self.processed_image, self.render_position, self.processed_image)


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
    elif widget_type == 'gauge':
        return GaugeWidget(config)
    elif widget_type == 'image':
        return ImageWidget(config)
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
