from PIL import Image, ImageDraw, ImageFont
import json
import numpy as np
from sklearn.cluster import KMeans

# Load colors from JSON
def load_colors(json_file, num_colors):
    print("Loading colors from JSON...")
    with open(json_file, "r", encoding="utf-8") as file:
        colors = json.load(file)
    
    rgb_values = []
    for color in colors:
        hex_code = color["Hex"].lstrip("#")
        rgb = tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))
        rgb_values.append(rgb)

    # Check if num_colors is 0, if so, return all colors without clustering
    if num_colors == 0:
        print(f"Using all colors without clustering...")
        clustered_palette = [{"RGB": rgb, "Symbol": chr(65 + i % 26), "DMC": color["DMC"], "Name": color["Name"]} for i, (rgb, color) in enumerate(zip(rgb_values, colors))]
        return clustered_palette
    
    print(f"Clustering {len(rgb_values)} colors into {num_colors} groups...")
    kmeans = KMeans(n_clusters=num_colors, n_init=10, random_state=42)
    labels = kmeans.fit_predict(rgb_values)
    
    clustered_palette = []
    symbols = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T"]  # Simple symbols

    # For each cluster, find the color information from the colors list
    for i in range(num_colors):
        # Find the index of the color that belongs to this cluster (i)
        cluster_indices = np.where(labels == i)[0]
        # Use the first color in the cluster for the palette (can change this logic as needed)
        first_color_idx = cluster_indices[0]
        color_info = colors[first_color_idx]
        
        # Add this color's info to the palette
        clustered_palette.append({
            "RGB": tuple(map(int, kmeans.cluster_centers_[i])),
            "Symbol": symbols[i % len(symbols)],
            "DMC": color_info["DMC"],
            "Name": color_info["Name"]
        })
    
    print(f"Reduced to {len(clustered_palette)} colors.")
    return clustered_palette


# Find closest color
def closest_color(pixel, color_palette):
    distances = [np.linalg.norm(np.array(pixel) - np.array(color["RGB"])) for color in color_palette]
    return color_palette[np.argmin(distances)]

# Get contrasting text color
def get_contrasting_color(rgb):
    r, g, b = rgb
    luminance = (0.299 * r + 0.587 * g + 0.114 * b)
    return "black" if luminance > 128 else "white"

# Convert image to cross-stitch pattern
def convert_image(input_image, output_image, width, colors_json, num_colors):
    print("Starting image processing...")
    color_palette = load_colors(colors_json, num_colors)
    
    img = Image.open(input_image)
    aspect_ratio = img.height / img.width
    new_height = int(width * aspect_ratio)
    print(f"Resizing image to {width}x{new_height}...")
    img = img.resize((width, new_height))
    img = img.convert("RGB")
    
    pixels = np.array(img)
    symbol_grid = []
    used_colors = set()  # To store unique colors used in the image
    print("Finding closest DMC colors...")
    
    for i in range(pixels.shape[0]):
        row_symbols = []
        for j in range(pixels.shape[1]):
            closest = closest_color(pixels[i, j], color_palette)
            row_symbols.append(closest["Symbol"])
            pixels[i, j] = closest["RGB"]
            used_colors.add(tuple(closest["RGB"]))  # Add the color to the set of used colors
        symbol_grid.append(row_symbols)
        print(f"Processed {i}/{pixels.shape[0]} rows...")
    
    print("Generating cross-stitch pattern image...")
    cell_size = 20
    pattern_img = Image.new("RGB", (width * cell_size, new_height * cell_size), "white")
    draw = ImageDraw.Draw(pattern_img)
    font = ImageFont.truetype("arial.ttf", 14)
    
    for i, row in enumerate(symbol_grid):
        for j, symbol in enumerate(row):
            x, y = j * cell_size, i * cell_size
            color = tuple(pixels[i, j])
            text_color = get_contrasting_color(color)
            draw.rectangle([x, y, x + cell_size, y + cell_size], fill=color, outline="black", width=1)
            
            # Calculate text size using textbbox
            bbox = draw.textbbox((0, 0), symbol, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Center the text inside the square
            text_x = x + (cell_size - text_width) // 2
            text_y = y + (cell_size - text_height) // 2
            draw.text((text_x, text_y), symbol, fill=text_color, font=font)
    
    pattern_img.save(output_image)
    print(f"Pattern saved to {output_image}")
    
    # Filter the color palette to only include colors used in the image
    used_palette = [color for color in color_palette if tuple(color["RGB"]) in used_colors]

    print("Generating color key...")
    key_img = Image.new("RGB", (500, len(used_palette) * 30), "white")  # Increase width for additional text
    draw = ImageDraw.Draw(key_img)
    
    # Use textbbox for the key as well
    for i, color in enumerate(used_palette):
        y = i * 30
        draw.rectangle([10, y + 5, 40, y + 25], fill=color["RGB"], outline="black")
        
        # Create the text string with Symbol, DMC, and Name
        text = f"{color['Symbol']} - {color['DMC']} - {color['Name']}"
        
        # Calculate text size using textbbox
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Write the text in the square
        text_x = 50
        text_y = y + (30 - text_height) // 2  # Center the text vertically
        draw.text((text_x, text_y), text, fill="black", font=font)
    
    key_img.save("key.png")
    print("Key saved as key.png")

# Example usage
convert_image("input.jpg", "output.png", 100, "colours.json", 0)  # 0 to use all colors
