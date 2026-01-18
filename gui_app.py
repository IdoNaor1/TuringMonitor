#!/usr/bin/env python3
"""
Turing Smart Screen - GUI Control Center
Professional GUI for controlling your Turing display
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
import json
import os
import sys
import subprocess
import threading
import time
from PIL import Image, ImageTk, ImageDraw
import pystray
from pystray import MenuItem as item

# Import monitor modules
try:
    from device_manager import TuringDisplay
    from monitor import get_all_metrics
    from renderer import Renderer
    import widgets
    import config as cfg
    import serial.tools.list_ports
except Exception as e:
    # If running as .exe or imports fail, create dummy config
    print(f"Warning: Could not import modules: {e}")
    class cfg:
        COM_PORT = "COM3"
        BAUD_RATE = 115200
        UPDATE_INTERVAL_MS = 1000
    TuringDisplay = None
    get_all_metrics = None
    Renderer = None
    widgets = None

# Load user settings from JSON if available
try:
    settings_path = os.path.join(os.path.expanduser("~"), ".turing_monitor_settings.json")
    if os.path.exists(settings_path):
        with open(settings_path, 'r') as f:
            user_settings = json.load(f)
            cfg.COM_PORT = user_settings.get("COM_PORT", cfg.COM_PORT)
            cfg.BAUD_RATE = user_settings.get("BAUD_RATE", cfg.BAUD_RATE)
            cfg.UPDATE_INTERVAL_MS = user_settings.get("UPDATE_INTERVAL_MS", cfg.UPDATE_INTERVAL_MS)
            print(f"Loaded user settings: COM_PORT={cfg.COM_PORT}, BAUD_RATE={cfg.BAUD_RATE}")
except Exception as e:
    print(f"Could not load user settings: {e}")

class TuringControlCenter:
    def __init__(self, root):
        self.root = root
        self.root.title("Turing Smart Screen Control Center")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        # Monitor state
        self.monitor_thread = None
        self.is_running = False
        self.display = None
        self.renderer = None

        # Layout designer state
        self.current_layout = None  # Currently loaded layout dict
        self.layout_file_path = None  # Path to current layout JSON
        self.layout_modified = False  # Unsaved changes flag
        self.preview_photo = None  # Tkinter PhotoImage for canvas
        self.preview_thread = None  # Background preview update thread
        self.preview_running = False  # Preview thread control flag
        self.positioning_mode = False  # Visual positioning active
        self.positioning_widget_id = None  # Widget being positioned
        self.dragging_widget = None  # Widget currently being dragged
        self.drag_start_x = 0  # Drag start X coordinate
        self.drag_start_y = 0  # Drag start Y coordinate
        self.drag_offset_x = 0  # Offset from widget origin
        self.drag_offset_y = 0  # Offset from widget origin

        # Window state
        self.is_hidden = False
        self.tray_icon = None
        self.should_exit = False

        # Set up window close handler to minimize to tray instead
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Create system tray icon
        self.create_tray_icon()

        # Create UI
        self.create_ui()

    def create_ui(self):
        """Create the main UI"""
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Tab 1: Monitor Control
        self.create_monitor_tab()

        # Tab 2: Layout Designer
        self.create_layout_tab()

        # Tab 3: Settings
        self.create_settings_tab()

        # Tab 4: Test & Diagnostics
        self.create_test_tab()

    def create_monitor_tab(self):
        """Create monitor control tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  Monitor Control  ")

        # Status Frame
        status_frame = ttk.LabelFrame(tab, text="Display Status", padding=15)
        status_frame.pack(fill='x', padx=10, pady=10)

        self.status_label = ttk.Label(status_frame, text="⚫ Stopped", font=('Arial', 14, 'bold'))
        self.status_label.pack()

        # Control Buttons Frame
        control_frame = ttk.LabelFrame(tab, text="Monitor Controls", padding=15)
        control_frame.pack(fill='x', padx=10, pady=10)

        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack()

        self.start_btn = ttk.Button(btn_frame, text="▶ Start Monitor", command=self.start_monitor, width=20)
        self.start_btn.grid(row=0, column=0, padx=5, pady=5)

        self.stop_btn = ttk.Button(btn_frame, text="⏹ Stop Monitor", command=self.stop_monitor, width=20, state='disabled')
        self.stop_btn.grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(btn_frame, text="➖ Minimize to Background", command=self.hide_window, width=20).grid(row=1, column=0, columnspan=2, padx=5, pady=5)

        # Layout Selection
        self.monitor_layout_frame = ttk.LabelFrame(tab, text="Select Layout", padding=15)
        self.monitor_layout_frame.pack(fill='both', expand=True, padx=10, pady=10)

        layouts = self.get_available_layouts()

        for i, layout_info in enumerate(layouts):
            layout_file, layout_name, description = layout_info

            frame = ttk.Frame(self.monitor_layout_frame)
            frame.pack(fill='x', pady=5)

            btn = ttk.Button(frame, text=f"🎨 {layout_name}",
                           command=lambda f=layout_file: self.start_with_layout(f),
                           width=25)
            btn.pack(side='left', padx=5)

            desc_label = ttk.Label(frame, text=description, foreground='gray')
            desc_label.pack(side='left', padx=5)

    def create_layout_tab(self):
        """Create layout designer tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  Layout Designer  ")

        # LEFT PANEL: Preview and Widget List
        left_panel = ttk.Frame(tab)
        left_panel.pack(side='left', fill='both', expand=False, padx=10, pady=10)

        # Preview canvas (480x720 = 1.5x scale of 320x480)
        ttk.Label(left_panel, text="Layout Preview (1.5x)", font=('Arial', 10, 'bold')).pack(anchor='w')

        canvas_frame = ttk.Frame(left_panel, relief='sunken', borderwidth=2)
        canvas_frame.pack(pady=5)

        self.preview_canvas = tk.Canvas(canvas_frame, width=480, height=720, bg='black', cursor='crosshair')
        self.preview_canvas.pack()

        # Bind drag and drop events
        self.preview_canvas.bind('<Button-1>', self.on_canvas_mouse_down)
        self.preview_canvas.bind('<B1-Motion>', self.on_canvas_drag)
        self.preview_canvas.bind('<ButtonRelease-1>', self.on_canvas_mouse_up)
        self.preview_canvas.bind('<Motion>', self.on_canvas_motion)
        self.preview_canvas.bind('<Double-Button-1>', self.on_canvas_double_click)

        # Coordinate display
        self.coord_label = ttk.Label(left_panel, text="Position: (0, 0)", font=('Arial', 9))
        self.coord_label.pack(anchor='w', pady=2)

        # Widget list
        ttk.Label(left_panel, text="Widgets:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(15, 5))

        list_frame = ttk.Frame(left_panel)
        list_frame.pack(fill='both', expand=True)

        self.widget_listbox = tk.Listbox(list_frame, height=10, selectmode='single')
        self.widget_listbox.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(list_frame, command=self.widget_listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.widget_listbox.config(yscrollcommand=scrollbar.set)

        # Double-click to edit widget
        self.widget_listbox.bind('<Double-Button-1>', lambda e: self.edit_widget())
        self.widget_listbox.bind('<<ListboxSelect>>', self.on_widget_list_select)

        # RIGHT PANEL: Controls
        controls_frame = ttk.Frame(tab)
        controls_frame.pack(side='right', fill='both', padx=10, pady=10)

        # Layout selection
        ttk.Label(controls_frame, text="Edit Layout:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=5)

        self.layout_var = tk.StringVar()
        self.layout_combo = ttk.Combobox(controls_frame, textvariable=self.layout_var, state='readonly', width=30)
        available_layouts = self.get_available_layouts()
        self.layout_combo['values'] = [f[1] for f in available_layouts]
        if len(available_layouts) > 0:
            self.layout_combo.current(0)
        self.layout_combo.pack(fill='x', pady=5)
        self.layout_combo.bind('<<ComboboxSelected>>', self.load_layout_preview)

        ttk.Button(controls_frame, text="📂 Load Layout", command=self.load_layout_preview).pack(fill='x', pady=5)

        # Background color
        ttk.Label(controls_frame, text="Background:", font=('Arial', 9, 'bold')).pack(anchor='w', pady=(15, 5))
        ttk.Button(controls_frame, text="🎨 Choose Background Color", command=self.choose_bg_color).pack(fill='x', pady=5)
        ttk.Button(controls_frame, text="🖼️ Set Background Image", command=self.choose_bg_image).pack(fill='x', pady=5)

        # Widget controls
        ttk.Label(controls_frame, text="Widgets:", font=('Arial', 9, 'bold')).pack(anchor='w', pady=(15, 5))
        ttk.Button(controls_frame, text="➕ Add Widget", command=self.add_widget).pack(fill='x', pady=5)
        ttk.Button(controls_frame, text="✏️ Edit Widget", command=self.edit_widget).pack(fill='x', pady=5)
        ttk.Button(controls_frame, text="🗑️ Remove Widget", command=self.remove_widget).pack(fill='x', pady=5)

        # Save
        ttk.Button(controls_frame, text="💾 Save Layout", command=self.save_layout, style='Accent.TButton').pack(fill='x', pady=(20, 5))
        ttk.Button(controls_frame, text="💾 Save As New...", command=self.save_layout_as).pack(fill='x', pady=5)

    def create_settings_tab(self):
        """Create settings tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  Settings  ")

        # Connection Settings
        conn_frame = ttk.LabelFrame(tab, text="Display Connection", padding=15)
        conn_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(conn_frame, text="COM Port:").grid(row=0, column=0, sticky='w', pady=5)
        self.port_var = tk.StringVar(value=cfg.COM_PORT)
        ttk.Entry(conn_frame, textvariable=self.port_var, width=15).grid(row=0, column=1, sticky='w', padx=5)
        ttk.Button(conn_frame, text="🔍 Scan Ports", command=self.scan_ports).grid(row=0, column=2, padx=5)

        ttk.Label(conn_frame, text="Baud Rate:").grid(row=1, column=0, sticky='w', pady=5)
        self.baud_var = tk.StringVar(value=str(cfg.BAUD_RATE))
        ttk.Entry(conn_frame, textvariable=self.baud_var, width=15).grid(row=1, column=1, sticky='w', padx=5)

        # Display Settings
        display_frame = ttk.LabelFrame(tab, text="Display Settings", padding=15)
        display_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(display_frame, text="Update Interval (ms):").grid(row=0, column=0, sticky='w', pady=5)
        self.interval_var = tk.StringVar(value=str(cfg.UPDATE_INTERVAL_MS))
        ttk.Entry(display_frame, textvariable=self.interval_var, width=15).grid(row=0, column=1, sticky='w', padx=5)

        ttk.Label(display_frame, text="Brightness (0-100):").grid(row=1, column=0, sticky='w', pady=5)
        self.brightness_var = tk.IntVar(value=50)
        brightness_scale = ttk.Scale(display_frame, from_=0, to=100, variable=self.brightness_var, orient='horizontal', length=200)
        brightness_scale.grid(row=1, column=1, sticky='w', padx=5)
        ttk.Button(display_frame, text="Apply", command=self.set_brightness).grid(row=1, column=2, padx=5)

        # Save Settings
        ttk.Button(tab, text="💾 Save All Settings", command=self.save_settings).pack(pady=20)

    def create_test_tab(self):
        """Create test & diagnostics tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  Test & Diagnostics  ")

        # Test Patterns
        test_frame = ttk.LabelFrame(tab, text="Display Test Patterns", padding=15)
        test_frame.pack(fill='x', padx=10, pady=10)

        colors = [
            ("Red", "#FF0000"),
            ("Green", "#00FF00"),
            ("Blue", "#0000FF"),
            ("White", "#FFFFFF"),
            ("Black", "#000000"),
            ("Cyan", "#00FFFF"),
            ("Magenta", "#FF00FF"),
            ("Yellow", "#FFFF00")
        ]

        row, col = 0, 0
        for name, color in colors:
            btn = ttk.Button(test_frame, text=f"⬜ {name}",
                           command=lambda c=color: self.test_color(c))
            btn.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
            col += 1
            if col > 3:
                col = 0
                row += 1

        # Diagnostics
        diag_frame = ttk.LabelFrame(tab, text="Diagnostics", padding=15)
        diag_frame.pack(fill='both', expand=True, padx=10, pady=10)

        ttk.Button(diag_frame, text="🔍 Test Connection", command=self.test_connection).pack(fill='x', pady=5)
        ttk.Button(diag_frame, text="📊 Show System Info", command=self.show_system_info).pack(fill='x', pady=5)
        ttk.Button(diag_frame, text="🔄 Clear Display", command=self.clear_display).pack(fill='x', pady=5)

        # Log
        ttk.Label(diag_frame, text="Log:", font=('Arial', 9, 'bold')).pack(anchor='w', pady=(10, 5))
        self.log_text = tk.Text(diag_frame, height=15, state='disabled')
        self.log_text.pack(fill='both', expand=True)

    # Methods
    def get_available_layouts(self):
        """Get list of available layouts"""
        layouts = []

        # Always use the permanent location for layouts
        # This ensures layouts are saved/loaded from a consistent location
        layout_dir = r"C:\Users\Ido\AppData\Local\Programs\TuringMonitor\layouts"

        layout_info = {
            "default.json": ("Default", "Classic green CPU / blue RAM bars"),
            "minimal.json": ("Minimal", "Large clock + CPU only"),
            "compact.json": ("Compact", "Space-efficient design"),
            "neon.json": ("Neon", "Cyberpunk cyan/magenta theme"),
            "clean.json": ("Clean", "Professional white theme")
        }

        if os.path.exists(layout_dir):
            for filename in os.listdir(layout_dir):
                if filename.endswith('.json'):
                    # Check if this is a built-in layout
                    if filename in layout_info:
                        name, desc = layout_info[filename]
                    else:
                        # For custom layouts, try to read the name from the JSON file
                        try:
                            with open(os.path.join(layout_dir, filename), 'r') as f:
                                layout_data = json.load(f)
                                name = layout_data.get('name', filename.replace('.json', '').replace('_', ' ').title())
                                desc = layout_data.get('description', "Custom layout")
                        except:
                            # Fallback to filename if we can't read the JSON
                            name = filename.replace('.json', '').replace('_', ' ').title()
                            desc = "Custom layout"

                    layouts.append((os.path.join(layout_dir, filename), name, desc))

        # If no layouts found, return dummy entry to prevent crash
        if not layouts:
            layouts.append(("", "No layouts found", "Please check installation"))

        return layouts

    def get_widget_at_position(self, x, y):
        """Find which widget is at the given canvas position"""
        if not self.current_layout:
            return None

        # Check widgets in reverse order (top to bottom rendering)
        for i in range(len(self.current_layout['widgets']) - 1, -1, -1):
            widget = self.current_layout['widgets'][i]
            wx = widget['position']['x']
            wy = widget['position']['y']
            ww = widget['size']['width']
            wh = widget['size']['height']

            # Check if click is inside widget bounds
            if wx <= x <= wx + ww and wy <= y <= wy + wh:
                return i

        return None

    def on_canvas_mouse_down(self, event):
        """Handle mouse down on canvas - start dragging widget"""
        if not self.current_layout:
            return

        # Convert from preview coordinates to actual
        actual_x = int(event.x / 1.5)
        actual_y = int(event.y / 1.5)
        actual_x = max(0, min(320, actual_x))
        actual_y = max(0, min(480, actual_y))

        # Find widget at this position
        widget_index = self.get_widget_at_position(actual_x, actual_y)

        if widget_index is not None:
            # Start dragging
            self.dragging_widget = widget_index
            widget = self.current_layout['widgets'][widget_index]
            self.drag_start_x = actual_x
            self.drag_start_y = actual_y
            self.drag_offset_x = actual_x - widget['position']['x']
            self.drag_offset_y = actual_y - widget['position']['y']
            self.preview_canvas.config(cursor='fleur')  # Move cursor

            # Select widget in listbox
            self.widget_listbox.selection_clear(0, tk.END)
            self.widget_listbox.selection_set(widget_index)
            self.widget_listbox.see(widget_index)

    def on_canvas_drag(self, event):
        """Handle dragging widget"""
        if self.dragging_widget is None or not self.current_layout:
            return

        # Convert to actual coordinates
        actual_x = int(event.x / 1.5)
        actual_y = int(event.y / 1.5)

        # Calculate new widget position (accounting for drag offset)
        new_x = actual_x - self.drag_offset_x
        new_y = actual_y - self.drag_offset_y

        # Clamp to canvas bounds
        widget = self.current_layout['widgets'][self.dragging_widget]
        max_x = 320 - widget['size']['width']
        max_y = 480 - widget['size']['height']
        new_x = max(0, min(max_x, new_x))
        new_y = max(0, min(max_y, new_y))

        # Update widget position
        widget['position']['x'] = new_x
        widget['position']['y'] = new_y

        # Redraw preview
        self.render_preview()

    def on_canvas_mouse_up(self, event):
        """Handle mouse release - finish dragging"""
        if self.dragging_widget is not None:
            # Finalize position
            self.layout_modified = True
            self.refresh_widget_list()

            widget = self.current_layout['widgets'][self.dragging_widget]
            self.log(f"Moved widget '{widget['id']}' to ({widget['position']['x']}, {widget['position']['y']})")

            self.dragging_widget = None
            self.preview_canvas.config(cursor='crosshair')

    def on_canvas_motion(self, event):
        """Show coordinates as mouse moves over canvas"""
        actual_x = int(event.x / 1.5)
        actual_y = int(event.y / 1.5)
        actual_x = max(0, min(320, actual_x))
        actual_y = max(0, min(480, actual_y))

        # Update coordinate display
        self.coord_label.config(text=f"Position: ({actual_x}, {actual_y})")

        # Change cursor if hovering over widget
        if not self.current_layout or self.dragging_widget is not None:
            return

        widget_index = self.get_widget_at_position(actual_x, actual_y)
        if widget_index is not None:
            self.preview_canvas.config(cursor='hand2')
        else:
            self.preview_canvas.config(cursor='crosshair')

    def on_canvas_double_click(self, event):
        """Handle double-click on canvas - open edit dialog if clicking on widget"""
        if not self.current_layout:
            return

        # Convert canvas coordinates to actual display coordinates
        actual_x = int(event.x / 1.5)
        actual_y = int(event.y / 1.5)
        actual_x = max(0, min(320, actual_x))
        actual_y = max(0, min(480, actual_y))

        # Check if we clicked on a widget
        widget_index = self.get_widget_at_position(actual_x, actual_y)
        if widget_index is not None:
            # Select the widget in the list
            self.widget_listbox.selection_clear(0, tk.END)
            self.widget_listbox.selection_set(widget_index)
            self.widget_listbox.see(widget_index)

            # Open edit dialog
            self.edit_widget()

    def on_widget_list_select(self, event=None):
        """Handle widget selection in list"""
        self.render_preview()  # Redraw with selection highlight

    def start_monitor(self):
        """Start the monitor"""
        if self.is_running:
            return

        self.log("Starting monitor...")

        # Run monitor in separate thread
        self.monitor_thread = threading.Thread(target=self._run_monitor_thread, args=(None,), daemon=True)
        self.monitor_thread.start()

        self.is_running = True
        self.status_label.config(text="🟢 Running", foreground='green')
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.log("Monitor started successfully!")

    def start_with_layout(self, layout_file):
        """Start monitor with specific layout"""
        if self.is_running:
            self.stop_monitor()
            # Give old thread time to fully release the port
            time.sleep(0.5)

        self.log(f"Starting monitor with layout: {os.path.basename(layout_file)}")

        # Run monitor in separate thread with specific layout
        self.monitor_thread = threading.Thread(target=self._run_monitor_thread, args=(layout_file,), daemon=True)
        self.monitor_thread.start()

        self.is_running = True
        self.status_label.config(text="🟢 Running", foreground='green')
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.log(f"Monitor started with {os.path.basename(layout_file)}!")

    def _run_monitor_thread(self, layout_file=None):
        """Thread function that runs the monitor loop"""
        try:
            # Check if modules are available
            if TuringDisplay is None or get_all_metrics is None or Renderer is None:
                self.log("Error: Required modules not available")
                self.log(f"TuringDisplay={TuringDisplay}, get_all_metrics={get_all_metrics}, Renderer={Renderer}")
                return

            # Initialize display with explicit port and baud rate
            self.log(f"Connecting to display: Port={cfg.COM_PORT}, Baud={cfg.BAUD_RATE}")
            self.display = TuringDisplay(port=cfg.COM_PORT, baud_rate=cfg.BAUD_RATE)

            if not self.display.connect():
                self.log("Error: Could not connect to display")
                self.log(f"Verify that COM port {cfg.COM_PORT} is available and not in use by another program")
                return

            self.log(f"Successfully connected to display at {cfg.COM_PORT}!")

            # Load layout
            if layout_file and os.path.exists(layout_file):
                self.renderer = Renderer(layout_file)
                self.log(f"Loaded layout: {os.path.basename(layout_file)}")
            else:
                # Use default layout
                default_layout = os.path.join(os.path.dirname(__file__), "layouts", "default.json")
                if getattr(sys, 'frozen', False):
                    default_layout = os.path.join(sys._MEIPASS, "layouts", "default.json")
                self.renderer = Renderer(default_layout)
                self.log("Loaded default layout")

            # Main loop
            frame_count = 0
            while self.is_running:
                try:
                    loop_start = time.time()

                    # Get metrics
                    data = get_all_metrics()

                    # Render image
                    image = self.renderer.render(data)

                    # Display (check if display is still connected)
                    if self.display is None:
                        self.log("Display disconnected, exiting loop...")
                        break
                    success = self.display.display_image(image)

                    # Calculate loop time and adjust sleep
                    loop_time = (time.time() - loop_start) * 1000  # Convert to ms

                    if frame_count % 10 == 0:
                        self.log(f"Frame {frame_count}: Display update {'OK' if success else 'FAIL'} (took {loop_time:.0f}ms)")

                    frame_count += 1

                    # Sleep for remaining time to maintain target interval
                    sleep_time = max(0, (cfg.UPDATE_INTERVAL_MS - loop_time) / 1000.0)
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                except Exception as e:
                    self.log(f"Error in monitor loop: {e}")
                    import traceback
                    self.log(traceback.format_exc())
                    time.sleep(1)

            # Cleanup
            self.log("Cleaning up display connection...")
            if self.display:
                self.display.disconnect()
                self.display = None
            self.log("Monitor thread exited cleanly")

        except Exception as e:
            self.log(f"Fatal error in monitor thread: {e}")
            import traceback
            self.log(traceback.format_exc())

    def stop_monitor(self):
        """Stop the monitor"""
        if not self.is_running:
            return

        self.log("Stopping monitor...")
        self.is_running = False

        # Wait for thread to finish and close connection properly
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.log("Waiting for monitor thread to finish...")
            self.monitor_thread.join(timeout=2.0)  # Wait up to 2 seconds

        # Ensure display is disconnected
        if self.display:
            try:
                self.display.disconnect()
            except:
                pass
            self.display = None

        self.monitor_thread = None

        self.status_label.config(text="⚫ Stopped", foreground='black')
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.log("Monitor stopped.")

    def test_color(self, color):
        """Test display with solid color"""
        self.log(f"Testing color: {color}")
        # Run test in thread to not block UI
        threading.Thread(target=self._test_color_thread, args=(color,), daemon=True).start()

    def _test_color_thread(self, color):
        """Thread for color test"""
        try:
            if TuringDisplay is None:
                self.log("Error: Display module not available")
                return

            display = TuringDisplay()
            if display.connect():
                # Parse hex color to RGB tuple
                rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
                img = Image.new('RGB', (320, 480), color=rgb)
                display.display_image(img)
                time.sleep(3)
                display.disconnect()
                self.log(f"Color test {color} complete")
            else:
                self.log("Error: Could not connect to display")
        except Exception as e:
            self.log(f"Error in color test: {e}")

    def test_connection(self):
        """Test connection to display"""
        self.log("Testing connection...")
        threading.Thread(target=self._test_connection_thread, daemon=True).start()

    def _test_connection_thread(self):
        """Thread for connection test"""
        try:
            if TuringDisplay is None:
                self.log("Error: Display module not available")
                return

            display = TuringDisplay()
            if display.connect():
                self.log("SUCCESS: Connected to Turing display!")
                self.log(f"Display: 320x480")
                display.disconnect()
            else:
                self.log("ERROR: Could not connect to display")
                self.log("Please check COM port in Settings tab")
        except Exception as e:
            self.log(f"Error testing connection: {e}")

    def scan_ports(self):
        """Scan for COM ports"""
        self.log("Scanning COM ports...")
        threading.Thread(target=self._scan_ports_thread, daemon=True).start()

    def _scan_ports_thread(self):
        """Thread for port scanning"""
        try:
            import serial.tools.list_ports

            ports = serial.tools.list_ports.comports()
            if not ports:
                self.log("No COM ports found")
                return

            self.log("=" * 60)
            self.log("Available COM Ports:")
            self.log("=" * 60)

            for i, port in enumerate(ports, 1):
                self.log(f"{i}. {port.device}")
                self.log(f"   Description: {port.description}")
                self.log(f"   Hardware ID: {port.hwid}")

                # Check if it's likely the Turing screen
                hwid_upper = port.hwid.upper()
                if "CH340" in hwid_upper or "CH552" in hwid_upper or "1A86" in hwid_upper:
                    self.log("   >>> ** POSSIBLE TURING SCREEN **")
                self.log("")

            self.log("Scan complete!")
        except Exception as e:
            self.log(f"Error scanning ports: {e}")

    def clear_display(self):
        """Clear the display"""
        self.test_color("#000000")

    def set_brightness(self):
        """Set display brightness"""
        level = self.brightness_var.get()
        self.log(f"Setting brightness to {level}%...")
        # Implementation here

    def show_system_info(self):
        """Show system information"""
        self.log("Gathering system information...")
        threading.Thread(target=self._show_system_info_thread, daemon=True).start()

    def _show_system_info_thread(self):
        """Thread for system info"""
        try:
            if get_all_metrics is None:
                self.log("Error: Monitor module not available")
                return

            metrics = get_all_metrics()
            self.log("=" * 60)
            self.log("System Metrics:")
            self.log("=" * 60)
            self.log(f"Time: {metrics['time']}")
            self.log(f"CPU Usage: {metrics['cpu_percent']:.1f}%")
            self.log(f"RAM Usage: {metrics['ram_used']:.2f} GB / {metrics['ram_total']:.2f} GB ({metrics['ram_percent']:.1f}%)")
            self.log("=" * 60)
        except Exception as e:
            self.log(f"Error getting system info: {e}")

    def render_preview(self):
        """Render current layout to preview canvas"""
        if not self.current_layout:
            return

        try:
            # Create temporary renderer
            temp_renderer = Renderer()
            temp_renderer.layout = self.current_layout
            temp_renderer.widget_instances = []

            # Create widget instances
            for widget_config in self.current_layout.get('widgets', []):
                try:
                    widget = widgets.create_widget(widget_config)
                    temp_renderer.widget_instances.append(widget)
                except Exception as e:
                    print(f"Preview widget error: {e}")

            # Get current metrics for live preview
            data = get_all_metrics()

            # Render at actual size (320x480)
            image_actual = temp_renderer.render(data)

            # Scale to 1.5x for display (480x720)
            image_scaled = image_actual.resize((480, 720), Image.Resampling.LANCZOS)

            # Convert to Tkinter PhotoImage
            self.preview_photo = ImageTk.PhotoImage(image_scaled)

            # Update canvas
            self.preview_canvas.delete('all')
            self.preview_canvas.create_image(240, 360, image=self.preview_photo)

            # Draw widget selection boxes if needed
            self.draw_widget_selection()

        except Exception as e:
            self.log(f"Preview render error: {e}")

    def draw_widget_selection(self):
        """Draw selection boxes around widgets on preview canvas"""
        # If a widget is selected in listbox, draw highlight box
        selection = self.widget_listbox.curselection()
        if not selection:
            return

        selected_index = selection[0]
        if selected_index >= len(self.current_layout.get('widgets', [])):
            return

        widget_config = self.current_layout['widgets'][selected_index]
        x = widget_config['position']['x'] * 1.5  # Scale to preview size
        y = widget_config['position']['y'] * 1.5
        w = widget_config['size']['width'] * 1.5
        h = widget_config['size']['height'] * 1.5

        # Draw selection rectangle
        self.preview_canvas.create_rectangle(x, y, x+w, y+h, outline='yellow', width=2, tags='selection')

    def start_preview_updates(self):
        """Start background thread for live preview updates"""
        if self.preview_running:
            return

        self.preview_running = True

        def update_loop():
            while self.preview_running:
                try:
                    self.render_preview()
                    time.sleep(2.0)  # Update every 2 seconds
                except:
                    pass

        self.preview_thread = threading.Thread(target=update_loop, daemon=True)
        self.preview_thread.start()

    def stop_preview_updates(self):
        """Stop background preview updates"""
        self.preview_running = False
        if self.preview_thread:
            self.preview_thread.join(timeout=3.0)

    def refresh_widget_list(self):
        """Update widget listbox with current layout widgets"""
        self.widget_listbox.delete(0, tk.END)

        if not self.current_layout:
            return

        for widget_config in self.current_layout.get('widgets', []):
            widget_id = widget_config.get('id', 'unnamed')
            widget_type = widget_config.get('type', 'unknown')
            x = widget_config['position']['x']
            y = widget_config['position']['y']

            display_text = f"[{widget_id}] {widget_type} at ({x}, {y})"
            self.widget_listbox.insert(tk.END, display_text)

    def load_layout_preview(self, event=None):
        """Load selected layout for editing"""
        # Check for unsaved changes
        if self.layout_modified:
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                "Current layout has unsaved changes. Save before loading new layout?"
            )
            if response is None:  # Cancel
                return
            elif response:  # Yes - save first
                self.save_layout()

        # Get selected layout
        layout_name = self.layout_var.get()
        available_layouts = self.get_available_layouts()

        layout_file = None
        for filename, name, desc in available_layouts:
            if name == layout_name:
                layout_file = filename
                break

        if not layout_file:
            self.log("Error: Could not find layout file")
            return

        # Load JSON
        try:
            with open(layout_file, 'r') as f:
                self.current_layout = json.load(f)

            self.layout_file_path = layout_file
            self.layout_modified = False

            self.log(f"Loaded layout: {layout_name}")

            # Update widget list
            self.refresh_widget_list()

            # Render preview
            self.render_preview()

            # Start live updates if not already running
            self.start_preview_updates()

        except Exception as e:
            self.log(f"Error loading layout: {e}")
            messagebox.showerror("Load Error", f"Failed to load layout: {e}")

    def choose_bg_color(self):
        """Choose and apply background color"""
        if not self.current_layout:
            messagebox.showwarning("No Layout", "Please load a layout first")
            return

        current_color = self.current_layout.get('display', {}).get('background_color', '#000000')
        color = colorchooser.askcolor(title="Choose Background Color", initialcolor=current_color)

        if color[1]:
            # Update layout
            if 'display' not in self.current_layout:
                self.current_layout['display'] = {}

            self.current_layout['display']['background_color'] = color[1]

            # Clear background image (mutually exclusive)
            if 'background_image' in self.current_layout['display']:
                del self.current_layout['display']['background_image']

            self.layout_modified = True
            self.render_preview()
            self.log(f"Background color set to: {color[1]}")

    def choose_bg_image(self):
        """Choose and apply background image"""
        if not self.current_layout:
            messagebox.showwarning("No Layout", "Please load a layout first")
            return

        filename = filedialog.askopenfilename(
            title="Select Background Image",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp")]
        )

        if not filename:
            return

        try:
            # Load and resize image
            img = Image.open(filename)
            img_resized = img.resize((320, 480), Image.Resampling.LANCZOS)

            # Save to layouts directory
            layout_name = self.layout_var.get().replace(' ', '_')
            bg_filename = f"bg_{layout_name}.png"

            if getattr(sys, 'frozen', False):
                layouts_dir = os.path.join(sys._MEIPASS, "layouts")
            else:
                layouts_dir = os.path.join(os.path.dirname(__file__), "layouts")

            bg_path = os.path.join(layouts_dir, bg_filename)
            img_resized.save(bg_path)

            # Update layout
            if 'display' not in self.current_layout:
                self.current_layout['display'] = {}

            self.current_layout['display']['background_image'] = bg_filename

            # Clear background color (image takes precedence)
            self.current_layout['display']['background_color'] = '#000000'

            self.layout_modified = True
            self.render_preview()
            self.log(f"Background image set: {bg_filename}")

        except Exception as e:
            messagebox.showerror("Image Error", f"Failed to load image: {e}")
            self.log(f"Background image error: {e}")

    def add_widget(self):
        """Open dialog to add new widget"""
        if not self.current_layout:
            messagebox.showwarning("No Layout", "Please load a layout first")
            return

        dialog = WidgetDialog(self.root, self.current_layout, mode='add')
        if dialog.result:
            # Add widget to layout
            self.current_layout['widgets'].append(dialog.result)
            self.layout_modified = True
            self.refresh_widget_list()
            self.render_preview()
            self.log(f"Added widget: {dialog.result['id']}")

    def edit_widget(self):
        """Open dialog to edit selected widget"""
        if not self.current_layout:
            messagebox.showwarning("No Layout", "Please load a layout first")
            return

        selection = self.widget_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a widget to edit")
            return

        widget_index = selection[0]
        dialog = WidgetDialog(self.root, self.current_layout, mode='edit', widget_index=widget_index)

        if dialog.result:
            if dialog.result.get('_delete'):
                # Delete was requested
                del self.current_layout['widgets'][widget_index]
                self.log(f"Deleted widget at index {widget_index}")
            else:
                # Update widget
                self.current_layout['widgets'][widget_index] = dialog.result
                self.log(f"Updated widget: {dialog.result['id']}")

            self.layout_modified = True
            self.refresh_widget_list()
            self.render_preview()

    def remove_widget(self):
        """Remove selected widget"""
        if not self.current_layout:
            messagebox.showwarning("No Layout", "Please load a layout first")
            return

        selection = self.widget_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a widget to remove")
            return

        widget_index = selection[0]
        widget_config = self.current_layout['widgets'][widget_index]
        widget_id = widget_config.get('id', 'unnamed')

        response = messagebox.askyesno("Confirm Delete",
                                      f"Delete widget '{widget_id}'?")
        if response:
            del self.current_layout['widgets'][widget_index]
            self.layout_modified = True
            self.refresh_widget_list()
            self.render_preview()
            self.log(f"Removed widget: {widget_id}")

    def validate_layout(self, layout):
        """Validate layout structure and content"""
        errors = []

        if not layout:
            return ["Layout is empty"]

        # Check required top-level fields
        if 'display' not in layout:
            errors.append("Missing 'display' configuration")
        if 'widgets' not in layout:
            errors.append("Missing 'widgets' array")
            return errors  # Can't continue without widgets

        # Validate display config
        display = layout.get('display', {})
        if 'width' not in display or 'height' not in display:
            errors.append("Display missing width or height")

        # Validate widgets
        widget_ids = set()
        valid_data_sources = ['time', 'date', 'cpu_percent', 'cpu_name', 'ram_percent',
                             'ram_used', 'ram_total', 'disk_c_percent', 'disk_c_used', 'disk_c_total',
                             'gpu_percent', 'gpu_name', 'gpu_temp', 'gpu_memory_percent', 'cpu_temp',
                             'net_upload_kbs', 'net_download_kbs', 'net_upload_mbs', 'net_download_mbs',
                             'uptime', 'hostname']

        for i, widget in enumerate(layout['widgets']):
            widget_num = i + 1

            # Check required fields
            if 'type' not in widget:
                errors.append(f"Widget {widget_num}: Missing 'type'")
                continue

            if 'id' not in widget:
                errors.append(f"Widget {widget_num}: Missing 'id'")
            else:
                # Check ID uniqueness
                if widget['id'] in widget_ids:
                    errors.append(f"Widget {widget_num}: Duplicate ID '{widget['id']}'")
                widget_ids.add(widget['id'])

            if 'position' not in widget:
                errors.append(f"Widget {widget_num}: Missing 'position'")
            else:
                pos = widget['position']
                if 'x' not in pos or 'y' not in pos:
                    errors.append(f"Widget {widget_num}: Position missing x or y")
                else:
                    if not (0 <= pos['x'] <= 320):
                        errors.append(f"Widget {widget_num}: X position {pos['x']} out of bounds (0-320)")
                    if not (0 <= pos['y'] <= 480):
                        errors.append(f"Widget {widget_num}: Y position {pos['y']} out of bounds (0-480)")

            if 'size' not in widget:
                errors.append(f"Widget {widget_num}: Missing 'size'")
            else:
                size = widget['size']
                if 'width' not in size or 'height' not in size:
                    errors.append(f"Widget {widget_num}: Size missing width or height")

            # Check data source validity
            if 'data_source' in widget:
                if widget['data_source'] not in valid_data_sources:
                    errors.append(f"Widget {widget_num}: Unknown data source '{widget['data_source']}'")

            # Validate widget type
            if widget['type'] not in ['text', 'progress_bar']:
                errors.append(f"Widget {widget_num}: Unknown widget type '{widget['type']}'")

            # Validate color codes (if present)
            color_fields = ['color', 'bar_color', 'background_color', 'text_color',
                           'border_color', 'gradient_end_color']
            for field in color_fields:
                if field in widget:
                    color = widget[field]
                    if not isinstance(color, str) or not color.startswith('#') or len(color) != 7:
                        errors.append(f"Widget {widget_num}: Invalid color format for '{field}': {color}")

        return errors

    def save_layout(self):
        """Save current layout to file"""
        if not self.current_layout or not self.layout_file_path:
            messagebox.showwarning("No Layout", "Please load a layout first")
            return

        # Validate layout
        errors = self.validate_layout(self.current_layout)
        if errors:
            error_msg = "Layout validation failed:\n\n" + "\n".join(errors[:5])  # Show first 5 errors
            if len(errors) > 5:
                error_msg += f"\n\n... and {len(errors) - 5} more errors"
            messagebox.showerror("Validation Error", error_msg)
            return

        try:
            # Write JSON
            with open(self.layout_file_path, 'w') as f:
                json.dump(self.current_layout, f, indent=2)

            self.layout_modified = False

            # Refresh layout list in case layout name changed
            self.refresh_layout_list()

            layout_name = os.path.basename(self.layout_file_path)
            self.log(f"Layout saved: {layout_name}")
            messagebox.showinfo("Success", f"Layout saved successfully!\n\n{layout_name}")

        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save layout: {e}")
            self.log(f"Save error: {e}")

    def save_layout_as(self):
        """Save layout as new file"""
        if not self.current_layout:
            messagebox.showwarning("No Layout", "Please load a layout first")
            return

        # Validate layout
        errors = self.validate_layout(self.current_layout)
        if errors:
            error_msg = "Layout validation failed:\n\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                error_msg += f"\n\n... and {len(errors) - 5} more errors"
            messagebox.showerror("Validation Error", error_msg)
            return

        # Get layouts directory - always use permanent location
        layouts_dir = r"C:\Users\Ido\AppData\Local\Programs\TuringMonitor\layouts"

        # File dialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            initialdir=layouts_dir,
            title="Save Layout As"
        )

        if not filename:
            return

        try:
            # Update layout name
            layout_name = os.path.splitext(os.path.basename(filename))[0]
            self.current_layout['name'] = layout_name.replace('_', ' ').title()

            # Write JSON
            with open(filename, 'w') as f:
                json.dump(self.current_layout, f, indent=2)

            # Update state
            self.layout_file_path = filename
            self.layout_modified = False

            # Refresh layout list in Monitor Control tab
            self.refresh_layout_list()

            # Log full path for debugging
            self.log(f"Layout saved as: {os.path.basename(filename)}")
            self.log(f"Full path: {filename}")
            messagebox.showinfo("Success", f"Layout saved!\n\nFile: {os.path.basename(filename)}\n\nPath: {os.path.dirname(filename)}")

        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save layout: {e}")
            self.log(f"Save error: {e}")

    def refresh_layout_list(self):
        """Refresh the layout dropdown and Monitor Control tab layouts"""
        # Get updated layout list
        layouts = self.get_available_layouts()

        # Update Layout Designer dropdown
        layout_names = [layout_info[1] for layout_info in layouts]
        self.layout_combo['values'] = layout_names

        # If a layout was just saved, try to select it
        if self.current_layout and 'name' in self.current_layout:
            saved_name = self.current_layout['name']
            if saved_name in layout_names:
                self.layout_combo.set(saved_name)

        # Refresh Monitor Control tab layout buttons
        # Clear existing buttons
        for widget in self.monitor_layout_frame.winfo_children():
            widget.destroy()

        # Recreate buttons
        for i, layout_info in enumerate(layouts):
            layout_file, layout_name, description = layout_info

            frame = ttk.Frame(self.monitor_layout_frame)
            frame.pack(fill='x', pady=5)

            btn = ttk.Button(frame, text=f"🎨 {layout_name}",
                           command=lambda f=layout_file: self.start_with_layout(f),
                           width=25)
            btn.pack(side='left', padx=5)

            desc_label = ttk.Label(frame, text=description, foreground='gray')
            desc_label.pack(side='left', padx=5)

        self.log("Layout list refreshed")

    def save_settings(self):
        """Save settings"""
        self.log("Saving settings...")
        try:
            # Update config in memory (will be used until app restarts)
            cfg.COM_PORT = self.port_var.get()
            cfg.BAUD_RATE = int(self.baud_var.get())
            cfg.UPDATE_INTERVAL_MS = int(self.interval_var.get())

            # Save to JSON file for persistence
            settings_path = os.path.join(os.path.expanduser("~"), ".turing_monitor_settings.json")
            settings = {
                "COM_PORT": cfg.COM_PORT,
                "BAUD_RATE": cfg.BAUD_RATE,
                "UPDATE_INTERVAL_MS": cfg.UPDATE_INTERVAL_MS
            }
            with open(settings_path, 'w') as f:
                json.dump(settings, f, indent=2)

            self.log(f"Settings saved successfully to {settings_path}")
            self.log(f"COM Port: {cfg.COM_PORT}")
            self.log(f"Baud Rate: {cfg.BAUD_RATE}")
            self.log(f"Update Interval: {cfg.UPDATE_INTERVAL_MS}ms")
            messagebox.showinfo("Success", "Settings saved! Changes will take effect immediately.")
        except Exception as e:
            self.log(f"Error saving settings: {e}")
            messagebox.showerror("Error", f"Failed to save settings: {e}")

    def log(self, message):
        """Add message to log"""
        self.log_text.config(state='normal')
        self.log_text.insert('end', f"{message}\n")
        self.log_text.see('end')
        self.log_text.config(state='disabled')

    def on_closing(self):
        """Handle window close - minimize to tray instead of exiting"""
        if self.is_running:
            # If monitor is running, just hide the window
            result = messagebox.askyesnocancel(
                "Minimize to Background",
                "Monitor is running. What would you like to do?\n\n"
                "Yes - Hide window and keep monitor running\n"
                "No - Stop monitor and exit\n"
                "Cancel - Return to app"
            )

            if result is True:  # Yes - hide window
                self.hide_window()
            elif result is False:  # No - stop and exit
                self.stop_monitor()
                self.root.destroy()
            # Cancel - do nothing
        else:
            # If monitor not running, just exit
            self.root.destroy()

    def create_tray_icon(self):
        """Create system tray icon"""
        # Create a simple icon (green circle)
        icon_image = Image.new('RGB', (64, 64), color='black')
        draw = ImageDraw.Draw(icon_image)
        draw.ellipse([8, 8, 56, 56], fill='#00FF00', outline='white', width=2)

        # Create tray menu
        menu = (
            item('Show Window', self.tray_show_window, default=True),
            item('Hide Window', self.tray_hide_window),
            pystray.Menu.SEPARATOR,
            item('Exit', self.tray_exit)
        )

        # Create icon
        self.tray_icon = pystray.Icon("turing_monitor", icon_image, "Turing Monitor", menu)

        # Run tray icon in background thread
        tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        tray_thread.start()

    def tray_show_window(self, icon=None, item=None):
        """Show window from tray"""
        self.root.after(0, self.show_window)

    def tray_hide_window(self, icon=None, item=None):
        """Hide window from tray"""
        self.root.after(0, self.hide_window)

    def tray_exit(self, icon=None, item=None):
        """Exit application from tray"""
        self.should_exit = True
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.after(0, self.exit_application)

    def exit_application(self):
        """Exit the application completely"""
        if self.is_running:
            self.stop_monitor()
        self.root.destroy()

    def hide_window(self):
        """Hide the main window"""
        self.root.withdraw()
        self.is_hidden = True
        self.log("Window hidden - monitor continues in background")
        self.log("Right-click the system tray icon to show window or exit")

    def show_window(self):
        """Show the main window"""
        self.root.deiconify()
        self.is_hidden = False
        self.root.lift()
        self.root.focus_force()


class WidgetDialog:
    """Dialog for adding/editing widgets"""

    def __init__(self, parent, layout, mode='add', widget_index=None):
        self.result = None
        self.layout = layout
        self.mode = mode
        self.widget_index = widget_index

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add Widget" if mode == 'add' else "Edit Widget")
        self.dialog.geometry("900x750")  # Wider to accommodate preview
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # If editing, load existing widget
        if mode == 'edit' and widget_index is not None:
            self.existing_widget = layout['widgets'][widget_index]
        else:
            self.existing_widget = None

        self.create_widgets()

        # Wait for dialog to close
        self.dialog.wait_window()

    def create_widgets(self):
        """Create dialog UI"""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill='both', expand=True)

        # Create two-column layout: form on left, preview on right
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))

        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side='right', fill='y')

        # Preview section (right side)
        preview_label = ttk.Label(right_frame, text="Preview", font=('Arial', 11, 'bold'))
        preview_label.pack(pady=(0, 10))

        # Preview canvas (160x240 = 320x480 at 0.5 scale for compact display)
        self.preview_canvas = tk.Canvas(right_frame, width=160, height=240, bg='black', highlightthickness=1, highlightbackground='gray')
        self.preview_canvas.pack()

        # Scrollable canvas for form (left side)
        canvas = tk.Canvas(left_frame)
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Basic Properties
        ttk.Label(scrollable_frame, text="Basic Properties", font=('Arial', 11, 'bold')).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0,10))

        # Widget Type
        row = 1
        ttk.Label(scrollable_frame, text="Widget Type:").grid(row=row, column=0, sticky='w', pady=5, padx=(0,10))
        self.type_var = tk.StringVar(value=self.existing_widget.get('type', 'text') if self.existing_widget else 'text')
        type_combo = ttk.Combobox(scrollable_frame, textvariable=self.type_var, values=['text', 'progress_bar'], state='readonly', width=25)
        type_combo.grid(row=row, column=1, sticky='w', pady=5)
        type_combo.bind('<<ComboboxSelected>>', self.on_type_change)

        # Widget ID
        row += 1
        ttk.Label(scrollable_frame, text="Widget ID:").grid(row=row, column=0, sticky='w', pady=5, padx=(0,10))
        self.id_var = tk.StringVar(value=self.existing_widget.get('id', '') if self.existing_widget else '')
        self.id_entry = ttk.Entry(scrollable_frame, textvariable=self.id_var, width=27)
        self.id_entry.grid(row=row, column=1, sticky='w', pady=5)
        if self.mode == 'edit':
            self.id_entry.config(state='disabled')  # Can't change ID

        # Data Source
        row += 1
        ttk.Label(scrollable_frame, text="Data Source:").grid(row=row, column=0, sticky='w', pady=5, padx=(0,10))
        data_sources = ['time', 'date', 'cpu_percent', 'cpu_name', 'ram_percent', 'ram_used', 'ram_total',
                       'disk_c_percent', 'disk_c_used', 'disk_c_total', 'gpu_percent', 'gpu_name', 'gpu_temp',
                       'gpu_memory_percent', 'cpu_temp', 'net_upload_kbs', 'net_download_kbs',
                       'net_upload_mbs', 'net_download_mbs', 'uptime', 'hostname']
        self.data_source_var = tk.StringVar(value=self.existing_widget.get('data_source', 'time') if self.existing_widget else 'time')
        self.data_source_var.trace_add('write', lambda *args: self.update_preview())
        source_combo = ttk.Combobox(scrollable_frame, textvariable=self.data_source_var, values=data_sources, width=25)
        source_combo.grid(row=row, column=1, sticky='w', pady=5)

        # Position
        row += 1
        ttk.Label(scrollable_frame, text="Position:", font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky='w', pady=(15,5))

        row += 1
        pos_frame = ttk.Frame(scrollable_frame)
        pos_frame.grid(row=row, column=0, columnspan=2, sticky='w', pady=5)

        ttk.Label(pos_frame, text="X:").pack(side='left', padx=(0,5))
        self.x_var = tk.IntVar(value=self.existing_widget['position']['x'] if self.existing_widget else 10)
        self.x_var.trace_add('write', lambda *args: self.update_preview())
        ttk.Spinbox(pos_frame, from_=0, to=320, textvariable=self.x_var, width=10).pack(side='left', padx=5)

        ttk.Label(pos_frame, text="Y:").pack(side='left', padx=(20,5))
        self.y_var = tk.IntVar(value=self.existing_widget['position']['y'] if self.existing_widget else 10)
        self.y_var.trace_add('write', lambda *args: self.update_preview())
        ttk.Spinbox(pos_frame, from_=0, to=480, textvariable=self.y_var, width=10).pack(side='left', padx=5)

        # Size
        row += 1
        size_frame = ttk.Frame(scrollable_frame)
        size_frame.grid(row=row, column=0, columnspan=2, sticky='w', pady=5)

        ttk.Label(size_frame, text="Width:").pack(side='left', padx=(0,5))
        self.width_var = tk.IntVar(value=self.existing_widget['size']['width'] if self.existing_widget else 300)
        self.width_var.trace_add('write', lambda *args: self.update_preview())
        ttk.Spinbox(size_frame, from_=10, to=320, textvariable=self.width_var, width=10).pack(side='left', padx=5)

        ttk.Label(size_frame, text="Height:").pack(side='left', padx=(20,5))
        self.height_var = tk.IntVar(value=self.existing_widget['size']['height'] if self.existing_widget else 50)
        self.height_var.trace_add('write', lambda *args: self.update_preview())
        ttk.Spinbox(size_frame, from_=10, to=480, textvariable=self.height_var, width=10).pack(side='left', padx=5)

        # Type-specific properties frame
        row += 1
        ttk.Separator(scrollable_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky='ew', pady=15)

        row += 1
        self.specific_frame = ttk.Frame(scrollable_frame)
        self.specific_frame.grid(row=row, column=0, columnspan=2, sticky='nsew')
        self.specific_frame_row = row

        # Populate type-specific fields
        self.on_type_change()

        # Buttons at bottom (outside scrollable area)
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side='bottom', pady=(10, 0))

        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(side='left', padx=5)

        if self.mode == 'edit':
            ttk.Button(button_frame, text="Delete Widget", command=self.on_delete).pack(side='left', padx=20)

        # Initial preview render
        self.dialog.after(100, self.update_preview)

    def update_preview(self):
        """Update the widget preview"""
        try:
            # Create a temporary widget config from current form values
            widget_config = self.build_widget_config()

            if not widget_config:
                # Show error message on canvas
                self.preview_canvas.delete('all')
                self.preview_canvas.create_text(80, 120, text="Invalid config", fill='red', font=('Arial', 10))
                return

            # Import required modules
            from PIL import Image, ImageTk, ImageDraw
            from widgets import TextWidget, ProgressBarWidget

            # Create a preview image (320x480)
            preview_img = Image.new('RGB', (320, 480), color='black')

            # Get background from layout if available
            if 'background_color' in self.layout.get('display', {}):
                bg_color = self.layout['display']['background_color']
                preview_img = Image.new('RGB', (320, 480), color=bg_color)

            # Create ImageDraw object for rendering
            draw = ImageDraw.Draw(preview_img)

            # Create and render the widget
            if widget_config['type'] == 'text':
                widget = TextWidget(widget_config)
            elif widget_config['type'] == 'progress_bar':
                widget = ProgressBarWidget(widget_config)
            else:
                return

            # Get sample data for preview (need to pass all data as dict)
            data = {widget_config['data_source']: self.get_sample_data(widget_config['data_source'])}
            widget.render(draw, preview_img, data)

            # Scale down for display (0.5x = 160x240)
            preview_img = preview_img.resize((160, 240), Image.Resampling.LANCZOS)

            # Convert to PhotoImage and display
            self.preview_photo = ImageTk.PhotoImage(preview_img)
            self.preview_canvas.delete('all')
            self.preview_canvas.create_image(0, 0, anchor='nw', image=self.preview_photo)

        except Exception as e:
            # Show error on canvas for debugging
            self.preview_canvas.delete('all')
            self.preview_canvas.create_text(80, 120, text=f"Error:\n{str(e)[:50]}", fill='red', font=('Arial', 9), width=150)

    def get_sample_data(self, data_source):
        """Get sample data for preview"""
        sample_values = {
            'time': '12:34:56',
            'date': '2026-01-18',
            'cpu_percent': 45.5,
            'cpu_name': 'Intel i7',
            'ram_percent': 67.2,
            'ram_used': 8.5,
            'ram_total': 16.0,
            'disk_c_percent': 55.0,
            'disk_c_used': 250,
            'disk_c_total': 500,
            'gpu_percent': 30.0,
            'gpu_name': 'NVIDIA RTX',
            'gpu_temp': 65,
            'gpu_memory_percent': 40.0,
            'cpu_temp': 55,
            'net_upload_kbs': 125.5,
            'net_download_kbs': 850.2,
            'net_upload_mbs': 0.12,
            'net_download_mbs': 0.85,
            'uptime': '5d 12h 34m',
            'hostname': 'PC-NAME'
        }
        return sample_values.get(data_source, 'N/A')

    def build_widget_config(self):
        """Build widget config from current form values"""
        try:
            config = {
                'type': self.type_var.get(),
                'id': self.id_var.get() or 'preview',
                'data_source': self.data_source_var.get(),
                'position': {
                    'x': self.x_var.get(),
                    'y': self.y_var.get()
                },
                'size': {
                    'width': self.width_var.get(),
                    'height': self.height_var.get()
                }
            }

            # Add type-specific properties (check if attributes exist)
            if config['type'] == 'text':
                if hasattr(self, 'font_size_var'):
                    config['font_size'] = self.font_size_var.get()
                    config['font_family'] = self.font_family_var.get()
                    config['bold'] = self.bold_var.get()
                    config['italic'] = self.italic_var.get()
                    config['color'] = self.text_color_var.get()
                    config['align'] = self.align_var.get()
                else:
                    # Default values for text widget
                    config['font_size'] = 24
                    config['font_family'] = 'arial'
                    config['bold'] = False
                    config['italic'] = False
                    config['color'] = '#FFFFFF'
                    config['align'] = 'left'
            elif config['type'] == 'progress_bar':
                if hasattr(self, 'label_var'):
                    config['label'] = self.label_var.get()
                    config['bar_color'] = self.bar_color_var.get()
                    config['background_color'] = self.bg_color_var.get()
                    config['text_color'] = self.pb_text_color_var.get()
                    config['show_percentage'] = self.show_percentage_var.get()
                    config['show_label'] = self.show_label_var.get()
                    if hasattr(self, 'gradient_var'):
                        config['gradient'] = self.gradient_var.get()
                        if config.get('gradient'):
                            config['gradient_end_color'] = self.gradient_end_var.get()
                        config['border_width'] = self.border_width_var.get()
                        config['border_color'] = self.border_color_var.get()
                        config['corner_radius'] = self.corner_radius_var.get()
                else:
                    # Default values for progress bar
                    config['label'] = 'CPU'
                    config['bar_color'] = '#00FF00'
                    config['background_color'] = '#333333'
                    config['text_color'] = '#FFFFFF'
                    config['show_percentage'] = True
                    config['show_label'] = True

            return config
        except Exception as e:
            print(f"build_widget_config error: {e}")
            return None

    def on_type_change(self, event=None):
        """Update UI based on widget type"""
        # Clear specific frame
        for widget in self.specific_frame.winfo_children():
            widget.destroy()

        widget_type = self.type_var.get()

        if widget_type == 'text':
            self.create_text_widget_fields()
        elif widget_type == 'progress_bar':
            self.create_progress_bar_fields()

        # Update preview after fields are created
        self.dialog.after(50, self.update_preview)

    def create_text_widget_fields(self):
        """Create fields specific to TextWidget"""
        ttk.Label(self.specific_frame, text="Text Widget Properties", font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0,10))

        # Font Size
        row = 1
        ttk.Label(self.specific_frame, text="Font Size:").grid(row=row, column=0, sticky='w', pady=5, padx=(0,10))
        self.font_size_var = tk.IntVar(value=self.existing_widget.get('font_size', 24) if self.existing_widget and self.existing_widget['type']=='text' else 24)
        self.font_size_var.trace_add('write', lambda *args: self.update_preview())
        ttk.Spinbox(self.specific_frame, from_=8, to=72, textvariable=self.font_size_var, width=10).grid(row=row, column=1, sticky='w', pady=5)

        # Font Family
        row += 1
        ttk.Label(self.specific_frame, text="Font Family:").grid(row=row, column=0, sticky='w', pady=5, padx=(0,10))
        self.font_family_var = tk.StringVar(value=self.existing_widget.get('font_family', 'arial') if self.existing_widget and self.existing_widget['type']=='text' else 'arial')
        self.font_family_var.trace_add('write', lambda *args: self.update_preview())
        fonts = ['arial', 'courier', 'times', 'consolas', 'verdana']
        ttk.Combobox(self.specific_frame, textvariable=self.font_family_var, values=fonts, state='readonly', width=25).grid(row=row, column=1, sticky='w', pady=5)

        # Bold/Italic
        row += 1
        style_frame = ttk.Frame(self.specific_frame)
        style_frame.grid(row=row, column=0, columnspan=2, sticky='w', pady=5)

        self.bold_var = tk.BooleanVar(value=self.existing_widget.get('bold', False) if self.existing_widget and self.existing_widget['type']=='text' else False)
        self.bold_var.trace_add('write', lambda *args: self.update_preview())
        ttk.Checkbutton(style_frame, text="Bold", variable=self.bold_var).pack(side='left', padx=5)

        self.italic_var = tk.BooleanVar(value=self.existing_widget.get('italic', False) if self.existing_widget and self.existing_widget['type']=='text' else False)
        self.italic_var.trace_add('write', lambda *args: self.update_preview())
        ttk.Checkbutton(style_frame, text="Italic", variable=self.italic_var).pack(side='left', padx=5)

        # Color
        row += 1
        ttk.Label(self.specific_frame, text="Text Color:").grid(row=row, column=0, sticky='w', pady=5, padx=(0,10))
        color_frame = ttk.Frame(self.specific_frame)
        color_frame.grid(row=row, column=1, sticky='w', pady=5)

        self.text_color_var = tk.StringVar(value=self.existing_widget.get('color', '#FFFFFF') if self.existing_widget and self.existing_widget['type']=='text' else '#FFFFFF')
        self.text_color_var.trace_add('write', lambda *args: self.update_preview())
        ttk.Entry(color_frame, textvariable=self.text_color_var, width=10).pack(side='left', padx=5)
        ttk.Button(color_frame, text="Pick", command=lambda: self.pick_color(self.text_color_var)).pack(side='left')

        # Alignment
        row += 1
        ttk.Label(self.specific_frame, text="Alignment:").grid(row=row, column=0, sticky='w', pady=5, padx=(0,10))
        self.align_var = tk.StringVar(value=self.existing_widget.get('align', 'left') if self.existing_widget and self.existing_widget['type']=='text' else 'left')
        self.align_var.trace_add('write', lambda *args: self.update_preview())
        ttk.Combobox(self.specific_frame, textvariable=self.align_var, values=['left', 'center', 'right'], state='readonly', width=25).grid(row=row, column=1, sticky='w', pady=5)

    def create_progress_bar_fields(self):
        """Create fields specific to ProgressBarWidget"""
        ttk.Label(self.specific_frame, text="Progress Bar Properties", font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0,10))

        # Label
        row = 1
        ttk.Label(self.specific_frame, text="Label:").grid(row=row, column=0, sticky='w', pady=5, padx=(0,10))
        self.label_var = tk.StringVar(value=self.existing_widget.get('label', 'CPU') if self.existing_widget and self.existing_widget['type']=='progress_bar' else 'CPU')
        self.label_var.trace_add('write', lambda *args: self.update_preview())
        ttk.Entry(self.specific_frame, textvariable=self.label_var, width=27).grid(row=row, column=1, sticky='w', pady=5)

        # Bar Color
        row += 1
        ttk.Label(self.specific_frame, text="Bar Color:").grid(row=row, column=0, sticky='w', pady=5, padx=(0,10))
        color_frame1 = ttk.Frame(self.specific_frame)
        color_frame1.grid(row=row, column=1, sticky='w', pady=5)

        self.bar_color_var = tk.StringVar(value=self.existing_widget.get('bar_color', '#00FF00') if self.existing_widget and self.existing_widget['type']=='progress_bar' else '#00FF00')
        self.bar_color_var.trace_add('write', lambda *args: self.update_preview())
        ttk.Entry(color_frame1, textvariable=self.bar_color_var, width=10).pack(side='left', padx=5)
        ttk.Button(color_frame1, text="Pick", command=lambda: self.pick_color(self.bar_color_var)).pack(side='left')

        # Background Color
        row += 1
        ttk.Label(self.specific_frame, text="Background:").grid(row=row, column=0, sticky='w', pady=5, padx=(0,10))
        color_frame2 = ttk.Frame(self.specific_frame)
        color_frame2.grid(row=row, column=1, sticky='w', pady=5)

        self.bg_color_var = tk.StringVar(value=self.existing_widget.get('background_color', '#333333') if self.existing_widget and self.existing_widget['type']=='progress_bar' else '#333333')
        self.bg_color_var.trace_add('write', lambda *args: self.update_preview())
        ttk.Entry(color_frame2, textvariable=self.bg_color_var, width=10).pack(side='left', padx=5)
        ttk.Button(color_frame2, text="Pick", command=lambda: self.pick_color(self.bg_color_var)).pack(side='left')

        # Text Color
        row += 1
        ttk.Label(self.specific_frame, text="Text Color:").grid(row=row, column=0, sticky='w', pady=5, padx=(0,10))
        color_frame3 = ttk.Frame(self.specific_frame)
        color_frame3.grid(row=row, column=1, sticky='w', pady=5)

        self.pb_text_color_var = tk.StringVar(value=self.existing_widget.get('text_color', '#FFFFFF') if self.existing_widget and self.existing_widget['type']=='progress_bar' else '#FFFFFF')
        self.pb_text_color_var.trace_add('write', lambda *args: self.update_preview())
        ttk.Entry(color_frame3, textvariable=self.pb_text_color_var, width=10).pack(side='left', padx=5)
        ttk.Button(color_frame3, text="Pick", command=lambda: self.pick_color(self.pb_text_color_var)).pack(side='left')

        # Gradient
        row += 1
        self.gradient_var = tk.BooleanVar(value=self.existing_widget.get('gradient', False) if self.existing_widget and self.existing_widget['type']=='progress_bar' else False)
        self.gradient_var.trace_add('write', lambda *args: self.update_preview())
        ttk.Checkbutton(self.specific_frame, text="Use Gradient", variable=self.gradient_var, command=self.toggle_gradient).grid(row=row, column=0, columnspan=2, sticky='w', pady=5)

        # Gradient End Color (conditional)
        row += 1
        self.gradient_label = ttk.Label(self.specific_frame, text="Gradient End:")
        self.gradient_color_frame = ttk.Frame(self.specific_frame)
        self.gradient_row = row

        self.gradient_end_var = tk.StringVar(value=self.existing_widget.get('gradient_end_color', '#FF0000') if self.existing_widget and self.existing_widget['type']=='progress_bar' else '#FF0000')
        self.gradient_end_var.trace_add('write', lambda *args: self.update_preview())
        ttk.Entry(self.gradient_color_frame, textvariable=self.gradient_end_var, width=10).pack(side='left', padx=5)
        ttk.Button(self.gradient_color_frame, text="Pick", command=lambda: self.pick_color(self.gradient_end_var)).pack(side='left')

        self.toggle_gradient()  # Show/hide gradient controls

        # Border Width
        row += 1
        ttk.Label(self.specific_frame, text="Border Width:").grid(row=row, column=0, sticky='w', pady=5, padx=(0,10))
        self.border_width_var = tk.IntVar(value=self.existing_widget.get('border_width', 0) if self.existing_widget and self.existing_widget['type']=='progress_bar' else 0)
        self.border_width_var.trace_add('write', lambda *args: self.update_preview())
        ttk.Spinbox(self.specific_frame, from_=0, to=10, textvariable=self.border_width_var, width=10).grid(row=row, column=1, sticky='w', pady=5)

        # Border Color
        row += 1
        ttk.Label(self.specific_frame, text="Border Color:").grid(row=row, column=0, sticky='w', pady=5, padx=(0,10))
        color_frame4 = ttk.Frame(self.specific_frame)
        color_frame4.grid(row=row, column=1, sticky='w', pady=5)

        self.border_color_var = tk.StringVar(value=self.existing_widget.get('border_color', '#FFFFFF') if self.existing_widget and self.existing_widget['type']=='progress_bar' else '#FFFFFF')
        self.border_color_var.trace_add('write', lambda *args: self.update_preview())
        ttk.Entry(color_frame4, textvariable=self.border_color_var, width=10).pack(side='left', padx=5)
        ttk.Button(color_frame4, text="Pick", command=lambda: self.pick_color(self.border_color_var)).pack(side='left')

        # Corner Radius
        row += 1
        ttk.Label(self.specific_frame, text="Corner Radius:").grid(row=row, column=0, sticky='w', pady=5, padx=(0,10))
        self.corner_radius_var = tk.IntVar(value=self.existing_widget.get('corner_radius', 0) if self.existing_widget and self.existing_widget['type']=='progress_bar' else 0)
        self.corner_radius_var.trace_add('write', lambda *args: self.update_preview())
        ttk.Spinbox(self.specific_frame, from_=0, to=20, textvariable=self.corner_radius_var, width=10).grid(row=row, column=1, sticky='w', pady=5)

        # Display Options
        row += 1
        ttk.Label(self.specific_frame, text="Display Options:", font=('Arial', 9, 'bold')).grid(row=row, column=0, columnspan=2, sticky='w', pady=(10,5))

        row += 1
        display_opts_frame = ttk.Frame(self.specific_frame)
        display_opts_frame.grid(row=row, column=0, columnspan=2, sticky='w', pady=5)

        self.show_percentage_var = tk.BooleanVar(value=self.existing_widget.get('show_percentage', True) if self.existing_widget and self.existing_widget['type']=='progress_bar' else True)
        self.show_percentage_var.trace_add('write', lambda *args: self.update_preview())
        ttk.Checkbutton(display_opts_frame, text="Show Percentage", variable=self.show_percentage_var).pack(side='left', padx=5)

        self.show_label_var = tk.BooleanVar(value=self.existing_widget.get('show_label', True) if self.existing_widget and self.existing_widget['type']=='progress_bar' else True)
        self.show_label_var.trace_add('write', lambda *args: self.update_preview())
        ttk.Checkbutton(display_opts_frame, text="Show Label", variable=self.show_label_var).pack(side='left', padx=5)

    def toggle_gradient(self):
        """Show/hide gradient end color based on checkbox"""
        if self.gradient_var.get():
            self.gradient_label.grid(row=self.gradient_row, column=0, sticky='w', pady=5, padx=(0,10))
            self.gradient_color_frame.grid(row=self.gradient_row, column=1, sticky='w', pady=5)
        else:
            self.gradient_label.grid_forget()
            self.gradient_color_frame.grid_forget()

    def pick_color(self, var):
        """Open color picker dialog"""
        color = colorchooser.askcolor(title="Choose Color", initialcolor=var.get())
        if color[1]:
            var.set(color[1])

    def validate(self):
        """Validate widget configuration"""
        # Check ID is unique (if adding)
        if self.mode == 'add':
            widget_id = self.id_var.get().strip()
            if not widget_id:
                messagebox.showerror("Validation Error", "Widget ID cannot be empty")
                return False

            # Check uniqueness
            for widget in self.layout['widgets']:
                if widget['id'] == widget_id:
                    messagebox.showerror("Validation Error", f"Widget ID '{widget_id}' already exists")
                    return False

        # Validate position
        if self.x_var.get() < 0 or self.x_var.get() > 320:
            messagebox.showerror("Validation Error", "X position must be between 0 and 320")
            return False

        if self.y_var.get() < 0 or self.y_var.get() > 480:
            messagebox.showerror("Validation Error", "Y position must be between 0 and 480")
            return False

        # Validate size
        if self.width_var.get() < 10 or self.height_var.get() < 10:
            messagebox.showerror("Validation Error", "Width and height must be at least 10 pixels")
            return False

        return True

    def on_ok(self):
        """Build widget config and close dialog"""
        if not self.validate():
            return

        # Build base config
        config = {
            'type': self.type_var.get(),
            'id': self.id_var.get().strip(),
            'position': {'x': self.x_var.get(), 'y': self.y_var.get()},
            'size': {'width': self.width_var.get(), 'height': self.height_var.get()},
            'data_source': self.data_source_var.get()
        }

        # Add type-specific properties
        if config['type'] == 'text':
            config['font_size'] = self.font_size_var.get()
            config['font_family'] = self.font_family_var.get()
            config['bold'] = self.bold_var.get()
            config['italic'] = self.italic_var.get()
            config['color'] = self.text_color_var.get()
            config['align'] = self.align_var.get()

        elif config['type'] == 'progress_bar':
            config['label'] = self.label_var.get()
            config['bar_color'] = self.bar_color_var.get()
            config['background_color'] = self.bg_color_var.get()
            config['text_color'] = self.pb_text_color_var.get()
            config['gradient'] = self.gradient_var.get()
            if config['gradient']:
                config['gradient_end_color'] = self.gradient_end_var.get()
            config['border_width'] = self.border_width_var.get()
            config['border_color'] = self.border_color_var.get()
            config['corner_radius'] = self.corner_radius_var.get()
            config['show_percentage'] = self.show_percentage_var.get()
            config['show_label'] = self.show_label_var.get()

        self.result = config
        self.dialog.destroy()

    def on_cancel(self):
        """Close dialog without saving"""
        self.result = None
        self.dialog.destroy()

    def on_delete(self):
        """Delete widget (edit mode only)"""
        if self.mode != 'edit':
            return

        response = messagebox.askyesno("Confirm Delete",
                                      f"Delete widget '{self.existing_widget['id']}'?")
        if response:
            self.result = {'_delete': True, 'index': self.widget_index}
            self.dialog.destroy()


def main():
    root = tk.Tk()
    app = TuringControlCenter(root)
    root.mainloop()


if __name__ == "__main__":
    main()
