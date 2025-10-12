import os
import json
import argparse
import datetime

CATEGORIES = {
    "datacall": {"read", "write", "pread", "pwrite", "pread64", "pwrite64", "mmap", "munmap"},
    "directorycall": {"mkdir", "mkdirat", "rmdir", "mknod", "mknodat"},
    "extendedattributecall": {"getxattr", "lgetxattr", "fgetxattr", "setxattr", "lsetxattr", "fsetxattr", "listxattr", "llistxattr", "flistxattr"},
    "metadatacall": {"open_variadic", "open", "creat", "creat64", "openat_variadic", "openat", "open64_variadic", "open64", "close", "sync", "statfs", "fstatfs", "statfs64", "fstatfs64", "unlink", "unlinkat", "rename", "renameat", "fopen", "fopen64", "fclose"},
    "specialcall": {"socket", "fcntl"}
}


def get_call_type(systemcall):
    for call_type, syscalls in CATEGORIES.items():
        if systemcall in syscalls:
            return call_type
    return "unknown"

def convert_nanoseconds_to_iso(nanoseconds):
    # Convert nanoseconds to seconds
    seconds = nanoseconds / 1_000_000_000
    # Create a datetime object from the seconds
    dt = datetime.datetime.fromtimestamp(seconds, tz=datetime.timezone.utc)
    # Convert to ISO 8601 format
    return dt.isoformat()


def convert_to_json(input_file, output_file):
    # Initialize a list to store all the entries
    entries = []

    # Open the input file for reading
    with open(input_file, 'r') as file:
        for line in file:
            # Split the line by commas
            fields = line.strip().split(',')

            # Extract values
            if len(fields) == 11:
                systemcall, timestamp, tid, pid, node, descriptor, path, new_path, offset, size, return_value = fields
                # entry = {
                #     "systemcall": systemcall,
                #     "timestamp": timestamp,
                #     "tid": tid,
                #     "pid": pid,
                #     "node": node,
                #     "descriptor": descriptor,
                #     "path": path,
                #     "new_path": new_path,
                #     "offset": offset,
                #     "size": size,
                #     "return_value": return_value
                # }

                entry = {
                    "systemcall": systemcall,
                    "type": get_call_type(systemcall),
                    "timestamp": convert_nanoseconds_to_iso(int(timestamp)),
                    # "timestamp": int(timestamp),
                    "tid": int(tid),
                    "pid": int(pid),
                    "node": node,
                    "descriptor": int(descriptor) if descriptor.strip() else None,
                    "path": path if path.strip() else None,
                    "new_path": new_path if new_path.strip() else None,
                    "offset": int(offset) if offset.strip() else None,
                    "size": int(size) if size.strip() else None,
                    "return_value": int(return_value) if return_value.strip().isdigit() else return_value if return_value.strip() else None
                }


                # Add the entry to the list
                entries.append(entry)
    
    # Write the entries to the output JSON file
    with open(output_file, 'w') as outfile:
        json.dump(entries, outfile, indent=4)


def convert_files_in_folder(input_folder, output_folder):
    # Create the output folder if it does not exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Iterate over each file in the input folder
    for filename in os.listdir(input_folder):
        input_file_path = os.path.join(input_folder, filename)
        
        # Check if it's a file (skip directories)
        if os.path.isfile(input_file_path):
            # Generate output file path
            output_file_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.json")
            
            # Convert the current file to JSON
            convert_to_json(input_file_path, output_file_path)
            print(f"Converted {filename} to JSON.")

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Convert files in a folder to JSON format.")
    parser.add_argument('input_folder', help="Path to the input folder containing the files to convert.")
    parser.add_argument('output_folder', help="Path to the output folder where the JSON files will be saved.")
    
    # Parse the arguments
    args = parser.parse_args()

    # Call the conversion function with the parsed arguments
    convert_files_in_folder(args.input_folder, args.output_folder)