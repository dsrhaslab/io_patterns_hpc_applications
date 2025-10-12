#!/bin/bash

# Path to the Python script that converts NVIDIA files to JSON
CONVERTER_SCRIPT="python3 ../convert_nvidia_to_json.py"

# Base directories (same structure as dstat)
SOURCE_BASE="../../results"
DEST_BASE="../../converted_results"

# Find all "nvidia" directories under the SOURCE_BASE
find "$SOURCE_BASE" -type d -name "nvidia" | while read -r nvidia_dir; do
    # Construct the corresponding output directory
    output_dir="${nvidia_dir/$SOURCE_BASE/$DEST_BASE}"
    
    # Ensure the output directory exists
    mkdir -p "$output_dir"

    # Check if the output directory is empty
    if [ "$(ls -A "$output_dir")" ]; then
        echo "Skipping: $output_dir is not empty."
        continue
    fi
    
    echo "Processing NVIDIA logs: $nvidia_dir -> $output_dir"
    
    # Run the conversion script with the correct arguments
    $CONVERTER_SCRIPT "$nvidia_dir" "$output_dir"
    
    # Handle success/failure
    if [ $? -eq 0 ]; then
        echo "Successfully processed NVIDIA logs: $nvidia_dir"
    else
        echo "Error processing NVIDIA logs: $nvidia_dir" >&2
    fi
done