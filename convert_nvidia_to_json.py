import os
import json
import sys
import re
from datetime import datetime, timezone

def convert_nanoseconds_to_iso(milliseconds):
    # Convert milliseconds to seconds
    seconds = milliseconds / 1000  # Change this line to divide by 1000
    # Create a datetime object from the seconds
    dt = datetime.fromtimestamp(seconds, tz=timezone.utc)
    # Convert to ISO 8601 format
    return dt.isoformat()

def sanitize_key(key):
    """Convert header names to valid JSON keys"""
    key = re.sub(r'[^a-zA-Z0-9_]', '_', key.lower())
    key = re.sub(r'_+', '_', key)
    return key.rstrip('_')

def parse_gpu_log_file(log_file, output_json):
    """Process a single NVIDIA-SMI log file"""
    entries = []
    
    with open(log_file, 'r') as infile:
        # Extract node name from filename (nvidia_<node>.csv -> <node>)
        
        node_name = os.path.splitext(os.path.basename(log_file))[0].split('_')[2]
        
        # Process header line
        header = infile.readline().strip()
        if not header:
            return  # Empty file
        
        raw_keys = [col.strip() for col in header.split(',')]
        keys = [sanitize_key(k) for k in raw_keys]
        
        # Process data lines
        for line in infile:
            line = line.strip()
            if not line:
                continue
                
            values = [v.strip() for v in line.split(',')]
            if len(values) != len(keys):
                continue  # Skip malformed lines
                
            entry = {'node': node_name}
            for key, value in zip(keys, values):
                if key == 'timestamp_ms':
                    entry['timestamp'] = convert_nanoseconds_to_iso(int(value))
                else:
                    try:
                        entry[key] = float(value) if '.' in value else int(value)
                    except ValueError:
                        entry[key] = value
                        
            entries.append(entry)
    
    with open(output_json, 'w') as outfile:
        json.dump(entries, outfile, indent=2)

def process_logs(input_folder, output_folder):
    """Process all log files in input folder"""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    for filename in os.listdir(input_folder):
        if filename.startswith('.'):
            continue  # Skip hidden files
        
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.json")
        
        if os.path.isfile(input_path):
            parse_gpu_log_file(input_path, output_path)
            print(f"Converted {filename} to JSON")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert_nvidia_logs.py <input_folder> <output_folder>")
        sys.exit(1)
    
    input_folder = sys.argv[1]
    output_folder = sys.argv[2]
    process_logs(input_folder, output_folder)