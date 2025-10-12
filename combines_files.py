import os
import sys
from collections import defaultdict
import json

def combine_files_in_directory(origin_dir, destination_dir):
    # Dictionary to hold lists of file contents by base name
    combined_files = defaultdict(list)

    # Iterate over all files in the specified origin directory
    for filename in os.listdir(origin_dir):
        if filename.endswith('.json'):  # Ensure we only process JSON files
            prefix = filename.split('_')[0]
            file_path = os.path.join(origin_dir, filename)

            # Read the content of the file and append it to the corresponding prefix
            with open(file_path, 'r') as f:
                # Load the JSON content
                try:
                    content = json.load(f)
                    combined_files[prefix].extend(content)  # Extend the list with the content
                except json.JSONDecodeError:
                    print(f"Error decoding JSON from file: {file_path}")

    # Write combined contents to new files in the destination directory
    for prefix, contents in combined_files.items():
        contents.sort(key=lambda x: x.get('timestamp'))  # Sort the list by timestamp
        output_file = os.path.join(destination_dir, f"{prefix}.json")
        with open(output_file, 'w') as outfile:
            json.dump(contents, outfile, indent=4)  # Write the combined list as JSON
        print(f"Combined file created: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python combine_files.py <origin_directory> <destination_directory>")
        sys.exit(1)

    origin_dir = sys.argv[1]
    destination_dir = sys.argv[2]

    if not os.path.exists(origin_dir):
        print(f"Origin directory '{origin_dir}' does not exist.")
        sys.exit(1)

    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    # Call the function with both the origin and destination directories
    combine_files_in_directory(origin_dir, destination_dir)