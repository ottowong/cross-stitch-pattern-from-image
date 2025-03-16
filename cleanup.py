import os
import time

# Get the base directory where the script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Paths for the uploads and output directories, using relative paths
UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

# Time threshold (24 hours ago)
TIME_THRESHOLD = time.time() - 24 * 60 * 60  # 24 hours ago

# List of files to not delete (e.g., .gitkeep files)
EXCLUDE_FILES = {'.gitkeep'}

def delete_old_files(directory):
    """Delete files older than 24 hours, except for excluded files like .gitkeep."""
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        
        # Skip directories and excluded files
        if os.path.isdir(file_path) or filename in EXCLUDE_FILES:
            continue
        
        file_age = os.path.getmtime(file_path)
        if file_age < TIME_THRESHOLD:
            print(f"Deleting {file_path}")
            os.remove(file_path)

def main():
    delete_old_files(UPLOADS_DIR)
    delete_old_files(OUTPUT_DIR)

if __name__ == "__main__":
    main()

