import os
import json
import argparse

def count_documents_in_subfolders(root_folder):
    subfolders = ['tracer', 'dstat', 'nvidia']
    subfolder_count = {}

    for subfolder in subfolders:

        total_count = 0
        full_subfolder_path = os.path.join(root_folder, subfolder)

        if not os.path.isdir(full_subfolder_path):
            print(f"Skipping missing folder: {full_subfolder_path}")
            continue

        for root, _, files in os.walk(full_subfolder_path):
            for file in files:
                if file.endswith(".json"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                total_count += len(data)
                            else:
                                print(f"Skipping {file_path}: top-level structure is not a list")
                    except Exception as e:
                        print(f"Error reading {file_path}: {e}")
        
        subfolder_count[subfolder] = total_count

    
    return subfolder_count


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Count the number of events.")
    parser.add_argument('input_folder', help="Path to the input folder containing the files with the events.")
    
    # Parse the arguments
    args = parser.parse_args()

    # Call the conversion function with the parsed arguments
    results = count_documents_in_subfolders(args.input_folder)

    for subfolder in  results:
        print("Total documents in " + subfolder + ": " + str(results[subfolder]))
