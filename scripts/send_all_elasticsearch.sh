#!/bin/bash

BASE_DIR="../../converted_results"
SCRIPT="../send_data_to_elasticsearch.py"

# Default values
DEFAULT_ES_URL="http://192.168.112.72:9200"
ES_URL="$DEFAULT_ES_URL"
ES_USER=""
ES_PASS=""

# Parse command line arguments
usage() {
    echo "Usage: $0 [-u ES_URL] [-U username] [-P password]"
    exit 1
}

while getopts ":u:U:P:" opt; do
  case $opt in
    u) ES_URL="$OPTARG" ;;
    U) ES_USER="$OPTARG" ;;
    P) ES_PASS="$OPTARG" ;;
    \?) echo "Invalid option: -$OPTARG" >&2; usage ;;
    :) echo "Option -$OPTARG requires an argument." >&2; usage ;;
  esac
done

# Validate authentication arguments
if [ -n "$ES_USER" ] || [ -n "$ES_PASS" ]; then
    if [ -z "$ES_USER" ] || [ -z "$ES_PASS" ]; then
        echo "Error: Both username (-U) and password (-P) must be provided if either is used." >&2
        exit 1
    fi
fi

# Prepare auth arguments array
AUTH_ARGS=()
if [ -n "$ES_USER" ] && [ -n "$ES_PASS" ]; then
    AUTH_ARGS=(--username "$ES_USER" --password "$ES_PASS")
fi

find "$BASE_DIR" -type d -mindepth 3 -print | while read -r dir; do
    # Extract components and verify structure
    if [[ "$dir" =~ ^$BASE_DIR/([^/]+)/([^/]+)/([^/]+)/?$ ]]; then
        app_name="${BASH_REMATCH[1]}"
        config_id="${BASH_REMATCH[2]}"
        run_number="${BASH_REMATCH[3]}"
        
        # Validate numeric run number
        if [[ "$run_number" =~ ^[0-9]+$ ]]; then
            session_name="${app_name}_${config_id}_run${run_number}"

            # Check if index exists
            CURL_AUTH=()
            if [ -n "$ES_USER" ] && [ -n "$ES_PASS" ]; then
                CURL_AUTH=(-u "${ES_USER}:${ES_PASS}")
            fi

            if curl "${CURL_AUTH[@]}" -X GET "${ES_URL}/_cat/indices" | grep "${session_name}"; then
                echo "Session ${session_name} already exists. Skipping."
            else
                echo "Processing $dir with session: $session_name"

                # Process both data types if they exist
                if [ -d "$dir/dstat" ]; then
                    python3 "$SCRIPT" -u "$ES_URL" --session "${session_name}" -d "$dir/dstat" "${AUTH_ARGS[@]}"
                fi

                if [ -d "$dir/nvidia" ]; then
                    python3 "$SCRIPT" -u "$ES_URL" --session "${session_name}" -d "$dir/nvidia" "${AUTH_ARGS[@]}"
                fi

                if [ -d "$dir/tracer" ]; then
                    python3 "$SCRIPT" -u "$ES_URL" --session "${session_name}" -d "$dir/tracer" "${AUTH_ARGS[@]}"
                fi

                sleep 10
            fi
        fi
    fi
done