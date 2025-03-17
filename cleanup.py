# This is an optional script that will clean up the uploads and output folder, since the main program doesn't manage that itself (yet?).
# You will probably want to schedule it to run on a timer for it to actually be useful.

import os
import time

# Time thresholds
UPLOADS_THRESHOLD = time.time() - 1 * 10 * 60 # 10 mins
OUTPUT_THRESHOLD = time.time() - 1 * 60 * 60 # 1 hour

# Get the base directory where the script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Paths for the uploads and output directories
UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

# List of files to not delete
EXCLUDE_FILES = {'.gitkeep'}

def delete_old_files(directory, threshold):
    """Delete files older than the specified threshold, except for excluded files."""
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        
        # Skip directories and excluded files
        if os.path.isdir(file_path) or filename in EXCLUDE_FILES:
            continue
        
        file_age = os.path.getmtime(file_path)
        if file_age < threshold:
            print(f"Deleting {file_path}")
            os.remove(file_path)

def main():
    delete_old_files(UPLOADS_DIR, UPLOADS_THRESHOLD)
    delete_old_files(OUTPUT_DIR, OUTPUT_THRESHOLD)

if __name__ == "__main__":
    main()
