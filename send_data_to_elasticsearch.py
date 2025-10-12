import argparse
import traceback
import json
import logging
import time
import os
from elasticsearch import Elasticsearch

logger = logging.getLogger("DoParser")
SENT_EVENTS = 0
SENT_BULKS = 0

def prepare_indices(es_conn, session):
    index = f"dio_trace_{session}"
    mappings = {
        "properties": {
            "return_value": {"type": "keyword"},
            "time_called": {"type": "date_nanos"},
            "usr": { "type": "float" },
            "sys": { "type": "float" },
            "idl": { "type": "float" },
            "wai": { "type": "float" },
            "stl": { "type": "float" },
            "dsk_read": { "type": "float" },
            "dsk_writ": { "type": "float" },
            "io_read": { "type": "float" },
            "io_writ": { "type": "float" },
            "net_recv": { "type": "float" },
            "net_send": { "type": "float" },
            "used": { "type": "float" },
            "free": { "type": "float" },
            "buff": { "type": "float" },
            "cach": { "type": "float" },
            "paging_in": { "type": "integer" },
            "paging_out": { "type": "integer" },
        }
    }
    es_conn.indices.create(index=index, mappings=mappings, ignore=400)
    return index

def bulk_index(es_conn, records, index, pipeline=None):
    bulk_arr = []
    for record in records:
        bulk_arr.append({'index': {}})  # Let Elasticsearch generate unique IDs
        bulk_arr.append(record)
    
    res = es_conn.bulk(index=index, body=bulk_arr, pipeline=pipeline)
    errors = {}
    for item in res.get('items', []):
        if 'error' in item.get('index', {}):
            error_reason = item['index']['error']['reason']
            errors[error_reason] = errors.get(error_reason, 0) + 1
    return errors, res["took"]

def process_file(es_conn, session, filepath, bulk_size, index):
    global SENT_EVENTS, SENT_BULKS
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            bulk = []
            for obj in data:
                if session:
                    obj["session_name"] = session
                elif "session_name" in obj:
                    session = obj["session_name"]
                
                bulk.append(obj)
                if len(bulk) >= bulk_size:
                    errors, took = bulk_index(es_conn, bulk, index)
                    if errors:
                        logger.error(f"Errors in bulk: {errors}")
                    else:
                        SENT_EVENTS += len(bulk)
                        SENT_BULKS += 1
                        logger.debug(f"Sent {len(bulk)} records in {took}ms")
                    bulk = []
            
            if bulk:
                errors, took = bulk_index(es_conn, bulk, index)
                if errors:
                    logger.error(f"Errors in final bulk: {errors}")
                else:
                    SENT_EVENTS += len(bulk)
                    SENT_BULKS += 1
                    logger.debug(f"Sent final {len(bulk)} records in {took}ms")
            
            logger.info(f"Processed {len(data)} records from {os.path.basename(filepath)}")

    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"Error processing {filepath}: {str(e)}")

def process_folder(es_conn, session, folder, bulk_size):
    if not os.path.isdir(folder):
        logger.error(f"Invalid folder: {folder}")
        return
    
    index = prepare_indices(es_conn, session)
    logger.info(f"Using index: {index}")
    
    for filename in sorted(os.listdir(folder)):
        if filename.endswith('.json'):
            filepath = os.path.join(folder, filename)
            process_file(es_conn, session, filepath, bulk_size, index)

def setup_logging():
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '[%(name)s][%(asctime)s] %(levelname)s %(message)s',
        datefmt='%a, %d %b %Y %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def main():
    setup_logging()
    start_time = time.time()
    
    parser = argparse.ArgumentParser(description='Process DIO trace files to Elasticsearch')
    parser.add_argument('-u', '--url', default="http://localhost:9200", help='Elasticsearch URL')
    parser.add_argument('--session', required=True, help='Session identifier')
    parser.add_argument('--size', type=int, default=1000, help='Bulk size')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('folder', help='Folder containing JSON files')
    parser.add_argument('--username', help='Elasticsearch username for basic authentication')
    parser.add_argument('--password', help='Elasticsearch password for basic authentication')
    
    args = parser.parse_args()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    try:

        basic_auth = None
        if args.username or args.password:
            if not (args.username and args.password):
                logger.error("Both --username and --password must be provided for basic authentication")
                exit(1)
            basic_auth = (args.username, args.password)

        es = Elasticsearch(
            args.url,
            basic_auth=basic_auth,
            verify_certs=False
        )
        logger.info(f"Connected to Elasticsearch: {es.ping()}")
        
        process_folder(es, args.session, args.folder, args.size)
        
        duration = time.time() - start_time
        logger.info(f"Processed {SENT_EVENTS} events in {SENT_BULKS} bulks")
        logger.info(f"Total time: {duration:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        traceback.print_exc()
        exit(1)

if __name__ == '__main__':
    main()