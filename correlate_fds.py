import argparse
import json
import logging

files_opened = 0
open_close_dif = 3

def check_open_close_threshold(logger):
    global files_opened
    global open_close_dif

    if files_opened > open_close_dif:
        logger.info(f'{files_opened} files are currently open')
    elif files_opened < 0:
        logger.info(f'The close system call was executed more times than the open system call')

def open_handler(trace_obj, fd_table, logger):  # create a new entry in the hash table if one doesn't exist yet 
    pid = trace_obj["pid"]
    fd = int(trace_obj["return_value"])
    path = trace_obj["path"]
    global files_opened
    
    if (pid, fd) not in fd_table and fd > 0:  # Check if FD is valid
        logger.debug(f'new key added to the hash table : {(pid, fd)} -> {path}')
        fd_table[(pid, fd)] = path
        trace_obj["file_path"] = path
        files_opened += 1
        check_open_close_threshold(logger)
    elif fd < 0:  # the open failed 
        logger.debug(f'failed to open file: {path} with descriptor: {(pid, fd)}')
    elif (pid, fd) in fd_table:
        logger.error(f'An open system call failed because the file descriptor {(pid, fd)} is already in use for file path: {fd_table[(pid, fd)]}')

def fopen_handler(trace_obj, fd_table, logger):  # create a new entry in the hash table if one doesn't exist yet 
    pid = trace_obj["pid"]

    if trace_obj["return_value"] != 0 and trace_obj["return_value"] != "file opened":  # Explicit check for empty string
        return
    
    fd = int(trace_obj["descriptor"])
    path = trace_obj["path"]
    global files_opened

    if (pid, fd) not in fd_table and fd > 0:  # Check if FD is valid
        logger.debug(f'new key added to the hash table : {(pid, fd)} -> {path}')
        fd_table[(pid, fd)] = path
        trace_obj["file_path"] = path
        files_opened += 1
        check_open_close_threshold(logger)
    elif fd < 0:  # the open failed 
        logger.debug(f'failed to open file: {path}  with descriptor: {(pid, fd)}')
    elif (pid, fd) in fd_table:
        logger.error(f'An open system call failed because the file descriptor {(pid, fd)} is already in use for file path: {fd_table[(pid, fd)]}')
    
    

def close_handler(trace_obj, fd_table, logger):  # Handle close system calls
    pid = trace_obj["pid"]
    fd = int(trace_obj["descriptor"])
    return_value = trace_obj["return_value"]
    global files_opened 

    if return_value >= 0 and (pid, fd) in fd_table:  # Check if the entry exists in the table and if the close doesn't return an error 
        path = fd_table.pop((pid, fd))
        trace_obj["file_path"] = path
        logger.debug(f'key has been removed from the hash table: {(pid, fd)} -> {path}')
        files_opened -= 1
        check_open_close_threshold(logger)
    elif return_value < 0:  # the close has returned with an error 
        logger.error(f'The system call close failed for file descriptor: {(pid, fd)}')
    elif (pid, fd) not in fd_table:
        logger.error(f'A close was attempted on file descriptor: {(pid, fd)} but this file descriptor isn\'t present in the hashtable')

def fork_handler(trace_obj, fd_table):
    parent_pid = trace_obj["pid"]
    return_value = trace_obj["return_value"]
    if return_value > 0:  # Means that this is the parent process and the fork was successful
        child_pid = return_value
        keys = list(fd_table.keys())
        for pid, fd in keys:
            if pid == parent_pid:
                fd_table[(child_pid, fd)] = fd_table[(pid, fd)]

def clone_handler(trace_obj, fd_table):
    parent_pid = trace_obj["pid"]
    return_value = trace_obj["return_value"] 
    if return_value > 0:
        child_pid = return_value
        flags = trace_obj["args"]["flags"]
        if "CLONE_FILES" in flags and "CLONE_THREAD" not in flags:
            keys = list(fd_table.keys())
            for pid, fd in keys:
                if pid == parent_pid:
                    fd_table[(child_pid, fd)] = fd_table[(pid, fd)]

def dup_handler(trace_obj, fd_table):
    return 0

def socket_handler(trace_obj, fd_table, logger):
    pid = trace_obj["pid"]
    fd = trace_obj["return_value"]
    if fd >= 0 and (pid,fd) not in fd_table:
        fd_table[(pid,fd)] = "socket"
        logger.debug(f'new key added to the hash table: {(pid,fd)} -> socket')
    elif fd < 0:  # the close has returned with an error 
        logger.error(f'The system call socket failed ')
    elif (pid,fd) in fd_table:
        logger.error(f'The system call socket returned fd {(pid,fd)} but this descriptor is already in the hash table')




def default_handler(trace_obj, fd_table, logger):  # Handler for non-critical or special system calls
    if "descriptor" in trace_obj:
        fd = trace_obj["descriptor"]
        pid = trace_obj["pid"]

        if (pid, fd) in fd_table and fd!=None:
            trace_obj["file_path"] = fd_table[(pid, fd)]
            logger.debug(f'The system call {trace_obj["systemcall"]} used the file descriptor {(pid, fd)} that corresponds to {fd_table[(pid, fd)]}')
        else:
            logger.error(f'The system call {trace_obj["systemcall"]} has tried to use the file descriptor {(pid, fd)} but this descriptor is not present in the hash table')
    return 0

# Handle different system calls 
def handle_call(fd_table, trace_obj, logger):
    sys_call = trace_obj["systemcall"]
    match sys_call:
        case "open":
            open_handler(trace_obj, fd_table, logger)  # Updates fd_table
            return trace_obj  # Return the modified trace object
        case "open64":
            open_handler(trace_obj, fd_table, logger)  # Updates fd_table
            return trace_obj
        case "openat":
            open_handler(trace_obj, fd_table, logger)  # Updates fd_table
            return trace_obj
        case "fopen":
            fopen_handler(trace_obj, fd_table, logger)  # Updates fd_table
            return trace_obj
        case "fopen64":
            fopen_handler(trace_obj, fd_table, logger)  # Updates fd_table
            return trace_obj
        case "socket":
            socket_handler(trace_obj,fd_table, logger)
            return trace_obj
        case "socketpair":
            print("socketpair")  # Not finished
            return trace_obj
        case "create":
            print("create")  # Not finished
            return trace_obj
        case "close":
            close_handler(trace_obj, fd_table, logger)  # Updates fd_table and trace_obj
            return trace_obj
        case "fclose":
            close_handler(trace_obj, fd_table, logger)  # Updates fd_table and trace_obj
            return trace_obj
        case "close64":
            close_handler(trace_obj, fd_table, logger)  # Updates fd_table and trace_obj
            return trace_obj
        case "fork":
            fork_handler(trace_obj, fd_table)
            return trace_obj
        case "dup":
            dup_handler(trace_obj, fd_table)
            return trace_obj
        case "clone":
            clone_handler(trace_obj, fd_table)
            return trace_obj
        case "vfork":
            fork_handler(trace_obj, fd_table)
            return trace_obj
       # case "read":
       #     return trace_obj  # Not finished
       # case "write":
       #     return trace_obj  # Not finished
        case _:
            default_handler(trace_obj, fd_table, logger)  # Updates fd_table and trace_obj
            return trace_obj  # Return the modified trace object

# Traverse through the trace file
def traverse_ordered_events(events, fd_table, logger):
    processed_events = []  # List to hold processed trace objects
    for trace_obj in events:
        if "systemcall" in trace_obj:
            processed_event = handle_call(fd_table, trace_obj, logger)
            processed_events.append(processed_event)  # Collect processed events
    return processed_events

def time_called(json):
    return json["timestamp"]

def order_trace_events(input_file):
    with open(input_file, "r") as file:
        # Load the entire JSON array from the file
        trace_objs = json.load(file)
    
    # Sort by timestamp
    trace_objs.sort(key=lambda x: x["timestamp"])
    return trace_objs

def main():
    # Define logging levels
    logger = logging.getLogger('File Path Correlate')
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler('correlate.log')
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    # Define argument parser
    parser = argparse.ArgumentParser(prog="Correlate File Descriptors", description="Script to correlate the file descriptors in system calls with the file paths")
    parser.add_argument("--input", required=True, help="file of traced events to correlate file paths")
    parser.add_argument("--output", required=True, help="output file to store updated trace")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging")

    # Parse arguments
    args = parser.parse_args()
    input_file = args.input
    out_file_path = args.output

    # Set logging level based on debug flag
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.ERROR)

    # Create file descriptor table
    fd_table = {}

    # Order the trace events before doing correlations 
    ordered_events = order_trace_events(input_file)
    logger.debug('Arguments parsed!')

    # Traverse ordered_events and collect processed events
    processed_events = traverse_ordered_events(ordered_events, fd_table, logger)

    # Write the processed events to the output file as a JSON array
    with open(out_file_path, "w") as out_file:  # Use 'with' to ensure the file is closed properly
        json.dump(processed_events, out_file, indent=4)  # Write as JSON array

    return 0

if __name__ == "__main__":
    main()