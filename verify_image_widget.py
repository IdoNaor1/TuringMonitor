
from PIL import Image, ImageDraw
import widgets
import os

def create_test_gif(filename):
    print(f"Creating test GIF: {filename}")
    frames = []
    colors = ['red', 'green', 'blue', 'yellow']
    for color in colors:
        img = Image.new('RGB', (50, 50), color=color)
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), color[0].upper(), fill='white')
        frames.append(img)
    
    frames[0].save(filename, save_all=True, append_images=frames[1:], duration=100, loop=0)
    print("GIF created.")

def test_image_widget():
    print("Testing Image Widget...")
    
    # Setup paths
    gif_path = "test_anim.gif"
    create_test_gif(gif_path)
    
    # Create canvas
    canvas = Image.new('RGB', (300, 200), color='black')
    draw = ImageDraw.Draw(canvas)
    
    # 1. Test Static Image (Scale: fit)
    print("Testing Static Image (fit)...")
    config_static = {
        'type': 'image',
        'id': 'static_test',
        'position': {'x': 10, 'y': 10},
        'size': {'width': 80, 'height': 80},
        'image_path': 'test_anim.gif', # It loads the first frame
        'scale_mode': 'fit'
    }
    widget_static = widgets.create_widget(config_static)
    widget_static.render(draw, canvas, {})
    
    # 2. Test Animated Image (Scale: stretch, 4 frames)
    print("Testing Animated Image...")
    config_anim = {
        'type': 'image',
        'id': 'anim_test',
        'position': {'x': 100, 'y': 10},
        'size': {'width': 80, 'height': 80},
        'image_path': gif_path,
        'scale_mode': 'stretch'
    }
    widget_anim = widgets.create_widget(config_anim)
    
    # Render 4 times at different positions to visualize frames (simulating time passing)
    for i in range(4):
        # Move y position for each frame to see them all
        widget_anim.position['y'] = 10 + (i * 25) # overlap a bit but show progress
        widget_anim.position['x'] = 150 + (i * 25)
        widget_anim.render(draw, canvas, {})
        print(f"Rendered frame {i}")
        
    # 3. Test Opacity
    print("Testing Opacity...")
    config_opacity = {
        'type': 'image',
        'id': 'opacity_test',
        'position': {'x': 10, 'y': 100},
        'size': {'width': 80, 'height': 80},
        'image_path': gif_path,
        'opacity': 0.5
    }
    widget_opacity = widgets.create_widget(config_opacity)
    widget_opacity.render(draw, canvas, {})

    # Save result
    output_file = "verify_image_widget_output.png"
    canvas.save(output_file)
    print(f"Verification output saved to {output_file}")
    
    # Clean up
    if os.path.exists(gif_path):
        os.remove(gif_path)

if __name__ == "__main__":
    try:
        test_image_widget()
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
