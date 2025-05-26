import os
import shutil

# Define the source and destination directories
source_dir = "/home/pi/allsky/config/myFiles/modules"  
destination_dir = "/home/pi/repos/allsky-modules"

# Ensure source directory exists
if not os.path.exists(source_dir):
    print(f"Source directory '{source_dir}' does not exist.")
    exit()

# Ensure destination directory exists
if not os.path.exists(destination_dir):
    print(f"Destination directory '{destination_dir}' does not exist.")
    exit()

# Loop through files in the source directory
for filename in os.listdir(source_dir):
        if filename.startswith("allsky_"):  # Check if the file matches the pattern
                if filename != 'allsky_base.py':
                        file_path = os.path.join(source_dir, filename)

                        if os.path.isfile(file_path):  # Ensure it's a file
                                folder_path = os.path.join(destination_dir, filename.replace('.py',''))  # Corresponding folder path

                                if os.path.exists(folder_path) and os.path.isdir(folder_path):  # Ensure folder exists
                                        shutil.copy(file_path, folder_path)
                                        print(f"Copied {filename} to {folder_path}")
                                else:
                                        print(f"Folder '{folder_path}' does not exist. Skipping {filename}.")


print("Copy operation completed.")