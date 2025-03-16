from PIL import Image
import json
import numpy as np

# Load colors from JSON
def load_colors(json_file):
    with open(json_file, "r", encoding="utf-8") as file:
        colors = json.load(file)
    
    # Convert hex to RGB and store with DMC info
    color_palette = []
    for color in colors:
        hex_code = color["Hex"].lstrip("#")
        rgb = tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))
        color_palette.append({"DMC": color["DMC"], "Name": color["Name"], "RGB": rgb})
    return color_palette

# Find the closest color
def closest_color(pixel, color_palette):
    pixel = np.array(pixel)
    distances = [np.linalg.norm(pixel - np.array(color["RGB"])) for color in color_palette]
    return color_palette[np.argmin(distances)]

# Process image
def convert_image(input_image, output_image, width, colors_json):
    color_palette = load_colors(colors_json)
    
    # Open image and resize while keeping aspect ratio
    img = Image.open(input_image)
    aspect_ratio = img.height / img.width
    new_height = int(width * aspect_ratio)
    img = img.resize((width, new_height))
    img = img.convert("RGB")
    
    # Convert each pixel to the closest DMC color
    pixels = np.array(img)
    for i in range(pixels.shape[0]):
        for j in range(pixels.shape[1]):
            closest = closest_color(pixels[i, j], color_palette)
            pixels[i, j] = closest["RGB"]
    
    # Save output image
    output_img = Image.fromarray(pixels.astype('uint8'), "RGB")
    output_img.save(output_image)

# Example usage
convert_image("input.jpg", "output.png", 100, "colours.json")