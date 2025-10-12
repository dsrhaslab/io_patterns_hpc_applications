#!/bin/bash -e
#SBATCH -e SCRIPT.err
#SBATCH -o SCRIPT.out
#SBATCH -J convert_all_tracer_to_json
#SBATCH -t 02:00:00
#SBATCH -p development
#SBATCH -N 1

# Paths to the Python scripts
CONVERTER_SCRIPT="python3 ../convert_tracer_to_json.py"
JOIN_FILES_SCRIPT="python3 ../combines_files.py"
CORRELATE_FDS_SCRIPT="python3 ../correlate_fds.py"

# Base directories
SOURCE_BASE="../../results"
DEST_BASE_TMP="../../converted_results_tmp"
DEST_BASE="../../converted_results"

# Find all "tracer" directories under the SOURCE_BASE
find "$SOURCE_BASE" -type d -name "tracer" | while read -r tracer_dir; do
    # Construct the corresponding output directory
    output_dir="${tracer_dir/$SOURCE_BASE/$DEST_BASE_TMP}"
    
    # Ensure the output directory exists
    mkdir -p "$output_dir"

    # Check if the output directory is empty
    if [ "$(ls -A "$output_dir")" ]; then
        echo "Skipping: $output_dir is not empty."
        continue
    fi
    
    echo "Processing: $tracer_dir -> $output_dir"
    
    # Run the conversion script with the correct arguments
    $CONVERTER_SCRIPT "$tracer_dir" "$output_dir"
    
    if [ $? -eq 0 ]; then
        echo "Successfully processed: $tracer_dir"
    else
        echo "Error processing: $tracer_dir"
    fi
done

find "$DEST_BASE_TMP" -type d -name "tracer" | while read -r tracer_dir; do

    output_dir="${tracer_dir/$DEST_BASE_TMP/$DEST_BASE}"

    # Ensure the output directory exists
    mkdir -p "$output_dir"

    # Check if the output directory is empty
    if [ "$(ls -A "$output_dir")" ]; then
        echo "Skipping: $output_dir is not empty."
        continue
    fi

    echo "Processing: $tracer_dir -> $output_dir"

    # Run the conversion script with the correct arguments
    $JOIN_FILES_SCRIPT "$tracer_dir" "$output_dir"

    if [ $? -eq 0 ]; then
        echo "Successfully processed: $tracer_dir"

        # Process each joined file with correlate-fds
        find "$output_dir" -type f | while read -r joined_file; do
            echo "Running correlate-fds on: $joined_file"
            $CORRELATE_FDS_SCRIPT --input "$joined_file" --output "$joined_file" -d
            if [ $? -eq 0 ]; then
                echo "Successfully correlated: $joined_file"
            else
                echo "Error correlating: $joined_file"
            fi
        done

    else
        echo "Error processing: $tracer_dir"
    fi


done
