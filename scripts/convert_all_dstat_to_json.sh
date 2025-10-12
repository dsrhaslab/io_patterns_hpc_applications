#!/bin/bash

# Path to the Python script that converts files to JSON
CONVERTER_SCRIPT="python3 ../convert_dstat_log.py"

# Base directories
SOURCE_BASE="../../results"
DEST_BASE="../../converted_results"

# Find all "tracer" directories under the SOURCE_BASE
find "$SOURCE_BASE" -type d -name "dstat" | while read -r dstat_dir; do
    # Construct the corresponding output directory
    output_dir="${dstat_dir/$SOURCE_BASE/$DEST_BASE}"
    
    # Ensure the output directory exists
    mkdir -p "$output_dir"

    # Check if the output directory is empty
    if [ "$(ls -A "$output_dir")" ]; then
        echo "Skipping: $output_dir is not empty."
        continue
    fi
    
    echo "Processing: $dstat_dir -> $output_dir"
    
    # Run the conversion script with the correct arguments
    $CONVERTER_SCRIPT "$dstat_dir" "$output_dir"
    
    if [ $? -eq 0 ]; then
        echo "Successfully processed: $dstat_dir"
    else
        echo "Error processing: $dstat_dir"
    fi
done
