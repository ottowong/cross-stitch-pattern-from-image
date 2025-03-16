import os
import time

# Get the base directory where the script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Paths for the uploads and output directories
UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

# Time thresholds
UPLOADS_THRESHOLD = time.time() - 1 * 10 * 60
OUTPUT_THRESHOLD = time.time() - 1 * 60 * 60

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