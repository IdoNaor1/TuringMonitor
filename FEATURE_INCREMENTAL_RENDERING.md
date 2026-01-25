# Feature Specification: Incremental/Differential Rendering

## Executive Summary

Implement incremental rendering to reduce display update time from ~1,600ms to ~200-300ms by only updating changed screen regions instead of sending the entire 320x480 frame buffer every cycle.

## Problem Statement

**Current Performance:**
- Full frame render: ~218ms (get_all_metrics + render)
- Device communication: ~1,397ms (sending 307,206 bytes via serial)
- **Total cycle time: ~1,615ms**

**Bottleneck Identified:**
The Turing display's serial communication is hardware-limited to ~1.36 seconds for full-frame updates, regardless of baud rate (tested 115200 to 2000000). This is the dominant bottleneck (86% of cycle time).

**Root Cause:**
Every update sends the complete 320x480 RGB565 frame buffer (307,200 bytes + 6 byte header) even when only small regions change (e.g., clock digits, CPU percentage).

## Solution: Incremental Rendering

Send only the changed rectangular regions to the display, reducing data transfer proportionally to the changed area.

### Performance Target

**Typical update scenario** (clock + CPU/RAM metrics):
- Clock widget: 100x50px = 10KB → ~44ms
- CPU bar: 300x30px = 18KB → ~80ms
- RAM bar: 300x30px = 18KB → ~80ms
- **Total: ~204ms (7.9x speedup)**

**Full refresh** (background change, layout update):
- Still use full-frame update: ~1,615ms

## Current Architecture

### Key Files
1. **renderer.py** - `Renderer` class, creates full-frame PIL Image
2. **device_manager.py** - `TuringDisplay.display_image()`, sends to device
3. **widgets.py** - Widget classes (TextWidget, ProgressBarWidget, SparklineWidget, ImageWidget)
4. **monitor.py** - Data collection with LHM caching (0.5s TTL)

### Display Protocol (device_manager.py)
The protocol **already supports partial updates**:
```python
# Header format includes coordinates
header[0] = x >> 2
header[1] = ((x & 3) << 6) + (y >> 4)
header[2] = ((y & 15) << 4) + (ex >> 6)
header[3] = ((ex & 63) << 2) + (ey >> 8)
header[4] = ey & 255
header[5] = Commands.DISPLAY_BITMAP  # Command 197
```

Where `x, y` = start position, `ex, ey` = end position (inclusive).

### Current Widget Rendering
Widgets have:
- `position`: {x, y}
- `size`: {width, height}
- `render(data)` method that returns PIL Image

Current flow:
1. Renderer creates blank 320x480 canvas
2. Each widget renders to its own Image
3. Widget image pasted onto canvas at position
4. Full canvas sent to device

## Implementation Plan

### Phase 1: Core Infrastructure

#### 1.1 Add Dirty Tracking to Widgets

**File: widgets.py**

Add to base widget behavior:
```python
class BaseWidget:
    def __init__(self, config):
        # Existing code...
        self._last_data_hash = None
        self._is_dirty = True
        self._last_update_time = 0
        self.update_interval = config.get('update_interval', 1)  # seconds
    
    def needs_update(self, data, current_time):
        """
        Determine if widget needs re-rendering.
        
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
            self._is_dirty = True
            return True
        
        return False
    
    def get_relevant_data(self, data):
        """
        Extract only the data this widget uses.
        Override in subclasses.
        """
        return data.get(self.data_source)
    
    def mark_clean(self, current_time):
        """Mark widget as up-to-date"""
        self._is_dirty = False
        self._last_update_time = current_time
    
    def mark_dirty(self):
        """Force widget to re-render on next update"""
        self._is_dirty = True
```

#### 1.2 Add Update Intervals to Widget Configs

**File: layouts/*.json**

Add optional `update_interval` to widget definitions:
```json
{
    "id": "clock",
    "type": "text",
    "data_source": "time",
    "update_interval": 1,
    "position": {"x": 10, "y": 10},
    ...
}
```

```json
{
    "id": "date",
    "type": "text", 
    "data_source": "date",
    "update_interval": 3600,
    "position": {"x": 10, "y": 50},
    ...
}
```

Default intervals by data source:
- Time: 1s
- CPU/GPU/RAM metrics: 1s
- Date: 3600s (1 hour)
- Static text: 0 (never update)
- Background image: 0 (never update)

#### 1.3 Create Incremental Renderer

**File: renderer.py**

Add new methods to Renderer class:
```python
class Renderer:
    def __init__(self):
        # Existing code...
        self.background_canvas = None  # Cache for static background
        self.widget_cache = {}  # Cache rendered widget images
        self.last_update_time = time.time()
    
    def render_incremental(self, data, force_full=False):
        """
        Render only changed regions.
        
        Args:
            data: Metrics data
            force_full: If True, re-render everything
        
        Returns:
            list: List of dirty regions with format:
                [{'x': int, 'y': int, 'width': int, 'height': int, 
                  'image': PIL.Image}, ...]
        """
        current_time = time.time()
        dirty_regions = []
        
        # First call or force full render
        if self.background_canvas is None or force_full:
            return self._full_render(data, current_time)
        
        # Check each widget for changes
        for widget in self.widget_instances:
            if widget.needs_update(data, current_time):
                # Render widget
                widget_img = widget.render(data)
                widget.mark_clean(current_time)
                
                # Composite onto background
                region_img = self._composite_widget_region(
                    widget_img, 
                    widget.config['position']['x'],
                    widget.config['position']['y']
                )
                
                dirty_regions.append({
                    'x': widget.config['position']['x'],
                    'y': widget.config['position']['y'],
                    'width': widget.config['size']['width'],
                    'height': widget.config['size']['height'],
                    'image': region_img
                })
        
        return dirty_regions
    
    def _full_render(self, data, current_time):
        """
        Perform full-frame render (existing render() logic).
        Returns as single dirty region covering entire screen.
        """
        full_image = self.render(data)  # Use existing method
        
        # Mark all widgets clean
        for widget in self.widget_instances:
            widget.mark_clean(current_time)
        
        # Cache background if static
        self.background_canvas = full_image.copy()
        
        return [{
            'x': 0,
            'y': 0,
            'width': 320,
            'height': 480,
            'image': full_image
        }]
    
    def _composite_widget_region(self, widget_img, x, y):
        """
        Composite widget onto background and return the region.
        Handles overlapping widgets and transparency.
        """
        # Extract background region
        bg_region = self.background_canvas.crop((
            x, y,
            x + widget_img.width,
            y + widget_img.height
        ))
        
        # Create composite
        composite = bg_region.copy()
        composite.paste(widget_img, (0, 0), widget_img if widget_img.mode == 'RGBA' else None)
        
        return composite
```

### Phase 2: Device Communication

#### 2.1 Add Partial Image Display Method

**File: device_manager.py**

Add new method:
```python
class TuringDisplay:
    def display_partial_image(self, image, x, y):
        """
        Display a partial image at specific coordinates.
        
        Args:
            image: PIL Image (any size)
            x, y: Top-left position on screen
        
        Returns:
            bool: Success status
        """
        if not self.connected:
            return False
        
        try:
            with self.lock:
                width, height = image.size
                
                # Convert to RGB565
                rgb565_data = self._image_to_rgb565(image)
                
                # Build header with partial coordinates
                ex = x + width - 1
                ey = y + height - 1
                
                header = bytearray(6)
                header[0] = x >> 2
                header[1] = ((x & 3) << 6) + (y >> 4)
                header[2] = ((y & 15) << 4) + (ex >> 6)
                header[3] = ((ex & 63) << 2) + (ey >> 8)
                header[4] = ey & 255
                header[5] = Commands.DISPLAY_BITMAP
                
                # Send
                self.serial.write(header)
                time.sleep(0.001)
                self.serial.write(rgb565_data)
                self.serial.flush()
                
                return True
                
        except Exception as e:
            print(f"Error displaying partial image: {e}")
            return False
    
    def display_dirty_regions(self, dirty_regions):
        """
        Display multiple dirty regions.
        
        Args:
            dirty_regions: List of region dicts from render_incremental()
        
        Returns:
            bool: Success status
        """
        if not dirty_regions:
            return True
        
        success = True
        for region in dirty_regions:
            result = self.display_partial_image(
                region['image'],
                region['x'],
                region['y']
            )
            success = success and result
        
        return success
```

### Phase 3: Integration

#### 3.1 Update Main Loop

**File: main.py (or gui_app.py for GUI mode)**

Modify monitor loop:
```python
# Setup
renderer = Renderer()
renderer.layout = layout
display = TuringDisplay()
display.connect()

# Configuration
FORCE_FULL_RENDER_INTERVAL = 300  # Full render every 5 minutes
last_full_render = 0

# Main loop
while True:
    loop_start = time.time()
    
    # Collect metrics
    data = monitor.get_all_metrics()
    
    # Decide render mode
    force_full = (time.time() - last_full_render) > FORCE_FULL_RENDER_INTERVAL
    
    # Render
    dirty_regions = renderer.render_incremental(data, force_full=force_full)
    
    # Send to display
    if len(dirty_regions) == 1 and dirty_regions[0]['x'] == 0 and dirty_regions[0]['y'] == 0:
        # Full frame update
        display.display_image(dirty_regions[0]['image'])
        last_full_render = time.time()
    else:
        # Incremental update
        display.display_dirty_regions(dirty_regions)
    
    # Timing
    loop_time = (time.time() - loop_start) * 1000
    print(f"Update: {len(dirty_regions)} regions, {loop_time:.0f}ms")
    
    time.sleep(max(0, (UPDATE_INTERVAL_MS - loop_time) / 1000))
```

#### 3.2 Add Configuration Options

**File: config.py**

```python
# === Incremental Rendering Settings ===
# Enable differential updates (only changed regions)
INCREMENTAL_RENDERING = True

# Force full render every N seconds (prevents artifacts)
FULL_RENDER_INTERVAL = 300  # 5 minutes

# Minimum region size for incremental update (bytes)
# Regions smaller than this will still be sent
MIN_INCREMENTAL_SIZE = 1000  # ~1KB
```

### Phase 4: Optimization

#### 4.1 Region Merging

Combine adjacent/overlapping dirty regions to reduce number of serial writes:

```python
def merge_regions(regions):
    """
    Merge overlapping or adjacent regions to minimize updates.
    
    Returns:
        list: Merged regions
    """
    if len(regions) <= 1:
        return regions
    
    # Sort by y then x
    sorted_regions = sorted(regions, key=lambda r: (r['y'], r['x']))
    
    merged = []
    current = sorted_regions[0].copy()
    
    for next_region in sorted_regions[1:]:
        # Check if regions overlap or are adjacent
        if (current['x'] + current['width'] >= next_region['x'] - 10 and
            current['y'] + current['height'] >= next_region['y'] - 10):
            # Merge
            current = merge_two_regions(current, next_region)
        else:
            merged.append(current)
            current = next_region.copy()
    
    merged.append(current)
    return merged
```

#### 4.2 Smart Update Intervals

Implement adaptive update rates based on change frequency:

```python
class AdaptiveWidget(BaseWidget):
    def __init__(self, config):
        super().__init__(config)
        self.change_history = []
        self.adaptive_interval = self.update_interval
    
    def adjust_interval(self):
        """Adjust update interval based on change frequency"""
        if len(self.change_history) < 10:
            return
        
        recent_changes = self.change_history[-10:]
        avg_change_rate = len([c for c in recent_changes if c]) / 10
        
        if avg_change_rate > 0.8:  # Changes frequently
            self.adaptive_interval = max(1, self.update_interval * 0.5)
        elif avg_change_rate < 0.2:  # Rarely changes
            self.adaptive_interval = min(60, self.update_interval * 2)
```

## Testing Requirements

### Unit Tests

1. **Widget dirty tracking**
   - Widget marks dirty on first render
   - Widget detects data changes
   - Widget respects update intervals
   - Widget caching works correctly

2. **Partial rendering**
   - Single widget update produces correct region
   - Multiple widgets produce multiple regions
   - Force full render works
   - Background caching works

3. **Region merging**
   - Adjacent regions merge correctly
   - Overlapping regions merge correctly
   - Non-overlapping regions stay separate

### Integration Tests

1. **Performance test**
   - Measure incremental vs full render times
   - Verify 5-8x speedup for typical updates
   - Ensure no memory leaks over 1000+ updates

2. **Visual correctness**
   - Screenshot comparison: incremental vs full render
   - No artifacts after 100 incremental updates
   - Full refresh clears any artifacts

3. **Edge cases**
   - All widgets static (no updates)
   - All widgets change every frame
   - Single pixel widget
   - Full-screen widget
   - Overlapping widgets
   - Transparent widgets

### Performance Benchmarks

Create test script: `test_incremental_perf.py`

```python
# Test scenarios:
# 1. Clock only update: ~50ms target
# 2. Clock + 2 progress bars: ~200ms target
# 3. Full frame: ~1600ms (baseline)
# 4. 100 incremental updates: measure avg, max, min
# 5. Memory usage over 1000 updates
```

## Edge Cases and Considerations

### 1. Overlapping Widgets
- **Problem:** Widget A covers part of Widget B. When B updates, need to re-render A's overlap.
- **Solution:** Track Z-order, re-render overlapping widgets when lower layers change.

### 2. Background Image Changes
- **Problem:** Background image update requires re-compositing all widgets.
- **Solution:** Force full render when background changes, rebuild cache.

### 3. Widget Resizing/Repositioning
- **Problem:** Widget moves, leaving old region visible.
- **Solution:** Track previous position, mark both old and new regions dirty.

### 4. Transparency/Alpha
- **Problem:** Transparent widgets need correct background compositing.
- **Solution:** Use RGBA mode, composite against cached background.

### 5. Serial Communication Errors
- **Problem:** Partial update fails, screen has artifacts.
- **Solution:** 
  - Implement retry logic
  - Force full render on error recovery
  - Periodic full refresh (every 5 minutes)

### 6. Memory Usage
- **Problem:** Caching background and widget images increases memory.
- **Solution:**
  - Monitor memory usage
  - Limit cache size
  - Clear cache on layout change

### 7. Layout Designer Compatibility
- **Problem:** GUI preview uses full render, needs incremental support.
- **Solution:** Add mode flag, GUI uses full render for preview.

## Rollout Strategy

### Phase 1: Implementation (Week 1)
1. Add dirty tracking to widgets
2. Implement render_incremental()
3. Add display_partial_image()
4. Basic integration in main loop

### Phase 2: Testing (Week 2)
1. Unit tests for all components
2. Performance benchmarking
3. Visual correctness verification
4. Bug fixes

### Phase 3: Optimization (Week 3)
1. Region merging
2. Adaptive intervals
3. Memory optimization
4. Fine-tuning

### Phase 4: Polish (Week 4)
1. Configuration options
2. Documentation
3. GUI integration
4. Release

## Success Metrics

**Primary:**
- Incremental update time: < 300ms (vs 1600ms baseline)
- 5x+ speedup for typical updates

**Secondary:**
- No visual artifacts after 100 updates
- Memory usage < 50MB additional
- Works with all widget types
- Backward compatible (can disable)

## Configuration Flag

Make feature opt-in initially:
```python
# config.py
INCREMENTAL_RENDERING = False  # Set True to enable

# Auto-enable if UPDATE_INTERVAL_MS < 1500
if UPDATE_INTERVAL_MS < 1500:
    INCREMENTAL_RENDERING = True
```

## Documentation Updates

1. **README.md** - Add section on incremental rendering
2. **PERFORMANCE.md** - Document benchmarks and tuning
3. **Widget docs** - Explain update_interval parameter
4. **Troubleshooting** - Common issues with incremental mode

## Future Enhancements

1. **Smart region batching** - Group regions by scan line
2. **Compression** - RLE or delta compression for regions
3. **Predictive rendering** - Pre-render expected next frame
4. **GPU acceleration** - Use PIL-SIMD or similar
5. **Network mode** - Stream updates over TCP vs serial

## References

- Current performance test: `test_loop_perf.py`
- Baud rate test: `test_baud_rates.py`
- Widget implementation: `widgets.py`
- Display protocol: `device_manager.py` lines 213-290
- Renderer: `renderer.py`

## Notes

- The 1.36s device communication time is **hardware-limited** and cannot be improved via baud rate
- Incremental rendering is the **only way** to achieve sub-500ms update times
- The LHM cache (0.5s TTL) is already optimized and working correctly
- This feature will be **most beneficial** for layouts with:
  - Many static elements (background, labels)
  - Few frequently-changing widgets (clock, metrics)
  - Large display area (320x480 = 153,600 pixels)
