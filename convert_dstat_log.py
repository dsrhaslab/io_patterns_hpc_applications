import os
import json
import sys
import re
from datetime import datetime, timezone

def convert_nanoseconds_to_iso(nanoseconds):
    # Convert nanoseconds to seconds
    seconds = nanoseconds / 1_000_000_000
    # Create a datetime object from the seconds
    dt = datetime.fromtimestamp(seconds, tz=timezone.utc)
    # Convert to ISO 8601 format
    return dt.isoformat()

def parse_number(value_str):
    value_str = value_str.strip().replace(',', '')  # Remove commas
    if not value_str:
        return 0
    # Extract numeric part and suffix
    match = re.match(r'^([\d.]+)([kMGB]?)(B?)$', value_str)
    if not match:
        return 0
    number, suffix, is_bytes = match.groups()
    number = float(number) if '.' in number else int(number)
    multiplier = {
        'k': 1024,
        'M': 1024**2,
        'G': 1024**3,
        'B': 1,
        '': 1
    }.get(suffix.upper(), 1)
    return int(number * multiplier) if suffix else number

def parse_log_file(log_file, output_json):
    entries = []
    
    with open(log_file, 'r') as infile:
        # Skip the first two header lines
        next(infile)
        next(infile)

        node_name = os.path.splitext(os.path.basename(log_file))[0].split('_')[2]
        
        for line in infile:
            line = line.strip()
            if re.match(r'^\d+\|', line):
                parts = line.split('|')
                if len(parts) < 8:
                    continue
                
                # Extract components from each section
                entry = {
                    "timestamp": convert_nanoseconds_to_iso(int(parts[0].strip())),
                    "node": node_name,
                    "usr": int(parts[1].split()[0].strip()),
                    "sys": int(parts[1].split()[1].strip()),
                    "idl": int(parts[1].split()[2].strip()),
                    "wai": int(parts[1].split()[3].strip()),
                    "stl": int(parts[1].split()[4].strip()),
                    "dsk_read": parse_number(parts[2].split()[0].strip()),
                    "dsk_writ": parse_number(parts[2].split()[1].strip()),
                    "io_read": float(parts[3].split()[0].strip()),
                    "io_writ": float(parts[3].split()[1].strip()),
                    "net_recv": parse_number(parts[4].split()[0].strip()),
                    "net_send": parse_number(parts[4].split()[1].strip()),
                    "used": parse_number(parts[5].split()[0].strip()),
                    "free": parse_number(parts[5].split()[1].strip()),
                    "buff": parse_number(parts[5].split()[2].strip()),
                    "cach": parse_number(parts[5].split()[3].strip()),
                    "paging_in": int(parts[6].split()[0].strip()),
                    "paging_out": int(parts[6].split()[1].strip()),
                    "ib_recv": parse_number(parts[7].split()[0].strip()),
                    "ib_send": parse_number(parts[7].split()[1].strip())
                }
                entries.append(entry)
    
    with open(output_json, 'w') as outfile:
        json.dump(entries, outfile, indent=2)

def process_logs(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    for filename in os.listdir(input_folder):
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, f"{filename}.json")
        
        if os.path.isfile(input_path):
            parse_log_file(input_path, output_path)
            print(f"Converted {filename} to JSON.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert_dstat_log.py <input_folder> <output_folder>")
        sys.exit(1)
    
    input_folder = sys.argv[1]
    output_folder = sys.argv[2]
    process_logs(input_folder, output_folder)