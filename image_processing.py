import os
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from sklearn.cluster import KMeans
from datetime import datetime

# Function to load colors from a JSON file and perform clustering
def load_colors(json_file, num_colors, log_buffers, user_id):
    log_buffers[user_id].append("Loading colors from JSON...")
    with open(json_file, "r", encoding="utf-8") as file:
        colors = json.load(file)
    
    rgb_values = []
    for color in colors:
        hex_code = color["Hex"].lstrip("#")
        rgb = tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))
        rgb_values.append(rgb)

    if num_colors == 0:
        log_buffers[user_id].append(f"Using all colors without clustering...")
        clustered_palette = [{"RGB": rgb, "Symbol": chr(65 + i % 26), "DMC": color["DMC"], "Name": color["Name"]} for i, (rgb, color) in enumerate(zip(rgb_values, colors))]
        return clustered_palette
    
    log_buffers[user_id].append(f"Clustering {len(rgb_values)} colors into {num_colors} groups...")
    kmeans = KMeans(n_clusters=num_colors, n_init=10, random_state=42)
    labels = kmeans.fit_predict(rgb_values)
    
    clustered_palette = []
    symbols = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]

    for i in range(num_colors):
        cluster_indices = np.where(labels == i)[0]
        first_color_idx = cluster_indices[0]
        color_info = colors[first_color_idx]
        
        clustered_palette.append({
            "RGB": tuple(map(int, kmeans.cluster_centers_[i])),
            "Symbol": symbols[i % len(symbols)],
            "DMC": color_info["DMC"],
            "Name": color_info["Name"]
        })
    
    log_buffers[user_id].append(f"Reduced to {len(clustered_palette)} colors.")
    return clustered_palette

# Function to find the closest color from the palette
def closest_color(pixel, color_palette):
    distances = [np.linalg.norm(np.array(pixel) - np.array(color["RGB"])) for color in color_palette]
    return color_palette[np.argmin(distances)]

# Function to get the contrasting text color (black or white)
def get_contrasting_color(rgb):
    r, g, b = rgb
    luminance = (0.299 * r + 0.587 * g + 0.114 * b)
    return "black" if luminance > 128 else "white"

# Function to process the image and generate pattern and key
def convert_image(input_image, width, colors_json, num_colors, user_id, log_buffers):
    log_buffers[user_id].append("Starting image processing...")
    color_palette = load_colors(colors_json, num_colors, log_buffers, user_id)
    
    img = Image.open(input_image)
    aspect_ratio = img.height / img.width
    new_height = int(width * aspect_ratio)
    log_buffers[user_id].append(f"Resizing image to {width}x{new_height}...")
    img = img.resize((width, new_height))
    img = img.convert("RGB")
    
    pixels = np.array(img)
    symbol_grid = []
    used_colors = set()
    log_buffers[user_id].append("Finding closest DMC colors...")
    
    for i in range(pixels.shape[0]):
        row_symbols = []
        for j in range(pixels.shape[1]):
            closest = closest_color(pixels[i, j], color_palette)
            row_symbols.append(closest["Symbol"])
            pixels[i, j] = closest["RGB"]
            used_colors.add(tuple(closest["RGB"]))
        symbol_grid.append(row_symbols)

        # Calculate progress percentage
        progress = (i + 1) / pixels.shape[0]
        bar_length = 20  # Adjust the length of the progress bar
        filled_length = int(bar_length * progress)
        progress_bar = "[" + "#" * filled_length + "-" * (bar_length - filled_length) + "]"
        
        log_buffers[user_id].append(f"Processed {i+1}/{pixels.shape[0]} rows... {progress_bar} {int(progress * 100)}%")

    
    # log_buffers[user_id].append("Generating cross-stitch pattern image...")
    cell_size = 20
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    pattern_filename = f"PATTERN_{timestamp}.png"
    pattern_img_path = os.path.join("output", pattern_filename)
    pattern_img = Image.new("RGB", (width * cell_size, new_height * cell_size), "white")
    draw = ImageDraw.Draw(pattern_img)
    font = ImageFont.truetype("arial.ttf", 14)
    
    for i, row in enumerate(symbol_grid):
        for j, symbol in enumerate(row):
            x, y = j * cell_size, i * cell_size
            color = tuple(pixels[i, j])
            text_color = get_contrasting_color(color)
            draw.rectangle([x, y, x + cell_size, y + cell_size], fill=color, outline="black", width=1)
            
            bbox = draw.textbbox((0, 0), symbol, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            text_x = x + (cell_size - text_width) // 2
            text_y = y + (cell_size - text_height) // 2
            draw.text((text_x, text_y), symbol, fill=text_color, font=font)
    
    pattern_img.save(pattern_img_path)
    
    used_palette = [color for color in color_palette if tuple(color["RGB"]) in used_colors]
    # log_buffers[user_id].append(f"Pattern saved as {pattern_filename}")

    key_filename = f"KEY_{timestamp}.png"
    key_img_path = os.path.join("output", key_filename)
    key_img = Image.new("RGB", (500, len(used_palette) * 30), "white")
    draw = ImageDraw.Draw(key_img)
    
    for i, color in enumerate(used_palette):
        y = i * 30
        draw.rectangle([10, y + 5, 40, y + 25], fill=color["RGB"], outline="black")
        text = f"{color['Symbol']} - {color['DMC']} - {color['Name']}"
        
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        text_x = 50
        text_y = y + (30 - text_height) // 2
        draw.text((text_x, text_y), text, fill="black", font=font)
    
    key_img.save(key_img_path)
    # log_buffers[user_id].append(f"Key saved as {key_filename}")
    log_buffers[user_id].append(f'COMPLETED {timestamp}')

    return pattern_img_path, key_img_path

def process_image(input_image, user_id, width, num_colors, log_buffers):
    pattern_img_path, key_img_path = convert_image(input_image, width, "colours.json", num_colors, user_id, log_buffers)
    #log_buffers[user_id].append(f"COMPLETED {datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}")