from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session, jsonify
import os
import time
import threading
from datetime import datetime
from image_processing import process_image

app = Flask(__name__)

app.secret_key = os.urandom(24)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

log_buffers = {}

# Stream logs by AJAX polling
@app.route('/get_logs')
def get_logs():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    user_id = session['user_id']
    logs = log_buffers.get(user_id, [])
    log_buffers[user_id] = []  # Clear the logs after sending
    return jsonify(logs)  # Return the logs as JSON

# Route for the log stream page
@app.route('/processing')
def processing():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    return render_template('processing.html')

# Route for the home page
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['image']
        size_type = request.form['size_type']
        size_value = int(request.form['size_value'])
        num_colors = int(request.form['num_colors'])

        if file:
            session['user_id'] = str(time.time())
            log_buffers[session['user_id']] = []
            
            input_image = os.path.join(app.config['UPLOAD_FOLDER'], f"{session['user_id']}.jpg")
            file.save(input_image)
            
            # Start processing
            threading.Thread(target=process_image, args=(input_image, session['user_id'], size_type, size_value, num_colors, log_buffers)).start()
            
            return redirect(url_for('processing'))
    
    return render_template('index.html')

# Route for the completed page
@app.route('/completed/<timestamp>')
def completed(timestamp):
    pattern_filename = f"PATTERN_{timestamp}.png"
    key_filename = f"KEY_{timestamp}.png"

    return render_template('completed.html', pattern=pattern_filename, key=key_filename)

# Route for the image files
@app.route('/output/<path:filename>')
def output_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
