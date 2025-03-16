from flask import Flask, render_template, request, redirect, url_for, send_from_directory, Response, session
import os
from PIL import Image, ImageDraw, ImageFont
import json
import numpy as np
from sklearn.cluster import KMeans
import time
import threading
from datetime import datetime
import base64

app = Flask(__name__)

# Secret key for session management
app.secret_key = os.urandom(24)

# Ensure that you have a 'uploads' and 'output' folder for saving uploaded images and generated files
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Initialize log storage per user session
log_buffers = {}

# Function to stream logs via SSE
def generate_log(user_id):
    while True:
        if user_id in log_buffers and log_buffers[user_id]:
            log_entry = log_buffers[user_id].pop(0)  # Get the next log entry for the user
            yield f"data: {log_entry}\n\n"
        time.sleep(0.5)  # Wait for a bit before checking again

# Modify load_colors to accept user_id explicitly
def load_colors(json_file, num_colors, user_id):
    log_buffers[user_id].append("Loading colors from JSON...")
    with open(json_file, "r", encoding="utf-8") as file:
        colors = json.load(file)
    
    rgb_values = []
    for color in colors:
        hex_code = color["Hex"].lstrip("#")
        rgb = tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))
        rgb_values.append(rgb)

    # Check if num_colors is 0, if so, return all colors without clustering
    if num_colors == 0:
        log_buffers[user_id].append(f"Using all colors without clustering...")
        clustered_palette = [{"RGB": rgb, "Symbol": chr(65 + i % 26), "DMC": color["DMC"], "Name": color["Name"]} for i, (rgb, color) in enumerate(zip(rgb_values, colors))]
        return clustered_palette
    
    log_buffers[user_id].append(f"Clustering {len(rgb_values)} colors into {num_colors} groups...")
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
    
    log_buffers[user_id].append(f"Reduced to {len(clustered_palette)} colors.")
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

def process_image(input_image, user_id):
    # Pass user_id explicitly to convert_image function
    pattern_img_path, key_img_path = convert_image(input_image, 100, "colours.json", 0, user_id)
    log_buffers[user_id].append(f"Pattern and Key generated.")
    log_buffers[user_id].append(f"Download Pattern: {url_for('download', filename=os.path.basename(pattern_img_path))}")
    log_buffers[user_id].append(f"Download Key: {url_for('download', filename=os.path.basename(key_img_path))}")

# Modify convert_image to accept user_id explicitly
def convert_image(input_image, width, colors_json, num_colors, user_id):
    log_buffers[user_id].append("Starting image processing...")
    color_palette = load_colors(colors_json, num_colors, user_id)  # Pass user_id here
    
    img = Image.open(input_image)
    aspect_ratio = img.height / img.width
    new_height = int(width * aspect_ratio)
    log_buffers[user_id].append(f"Resizing image to {width}x{new_height}...")
    img = img.resize((width, new_height))
    img = img.convert("RGB")
    
    pixels = np.array(img)
    symbol_grid = []
    used_colors = set()  # To store unique colors used in the image
    log_buffers[user_id].append("Finding closest DMC colors...")
    
    for i in range(pixels.shape[0]):
        row_symbols = []
        for j in range(pixels.shape[1]):
            closest = closest_color(pixels[i, j], color_palette)
            row_symbols.append(closest["Symbol"])
            pixels[i, j] = closest["RGB"]
            used_colors.add(tuple(closest["RGB"]))  # Add the color to the set of used colors
        symbol_grid.append(row_symbols)
        log_buffers[user_id].append(f"Processed {i}/{pixels.shape[0]} rows...")
    
    log_buffers[user_id].append("Generating cross-stitch pattern image...")
    cell_size = 20
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    # Save Pattern image to the "output" folder with the timestamp
    pattern_filename = f"PATTERN_{timestamp}.png"
    pattern_img_path = os.path.join(app.config['OUTPUT_FOLDER'], pattern_filename)
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
    
    pattern_img.save(pattern_img_path)
    
    # Filter the color palette to only include colors used in the image
    used_palette = [color for color in color_palette if tuple(color["RGB"]) in used_colors]

    log_buffers[user_id].append(f"Pattern saved as {pattern_filename}")

    # Save Key image to the "output" folder with timestamp
    key_filename = f"KEY_{timestamp}.png"
    key_img_path = os.path.join(app.config['OUTPUT_FOLDER'], key_filename)
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
    
    key_img.save(key_img_path)

    log_buffers[user_id].append(f"Key saved as {key_filename}")

    # Return the links to pattern and key
    return pattern_img_path, key_img_path

# Route for serving SSE logs (owner-only)
@app.route('/log_stream')
def log_stream():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return Response(generate_log(session['user_id']), content_type='text/event-stream')

# Main route to upload and process the image
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['image']
        if file:
            # Create a unique user ID for the session to track logs
            session['user_id'] = str(time.time())
            log_buffers[session['user_id']] = []
            
            # Save uploaded image
            input_image = os.path.join(app.config['UPLOAD_FOLDER'], f"{session['user_id']}.jpg")
            file.save(input_image)
            
            # Start processing in a new thread to allow multiple tasks
            threading.Thread(target=process_image, args=(input_image, session['user_id'],)).start()
            return redirect(url_for('log_stream'))  # Redirect to log stream page
    return render_template('index.html')  # Upload form

# Route to download the generated files
@app.route('/output/<filename>')
def download_file(filename):
    # Serve the file from the output folder
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
