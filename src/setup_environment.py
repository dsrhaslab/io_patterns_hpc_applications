#### 0.1. Install all needed dependencies

import os
import logging
from logging.handlers import RotatingFileHandler
from sklearn.preprocessing import LabelEncoder, OneHotEncoder


base_dir = '../converted_results/'
models_dir = "AutogluonModels/"

ALL_SYSTEMCALLS = ['read', 'write', 'pread', 'pwrite', 'pread64', 'pwrite64', 'mmap', 'munmap', 'mkdir', 'mkdirat', 
                   'rmdir', 'mknod', 'mknodat', 'getxattr', 'lgetxattr', 'fgetxattr', 'setxattr', 'lsetxattr', 'fsetxattr', 
                   'listxattr', 'llistxattr', 'flistxattr', 'open_var', 'open', 'creat', 'creat64', 'openat_var', 'openat', 
                   'close', 'sync', 'statfs', 'fstatfs', 'statfs64', 'fstatfs64', 'unlink', 'unlinkat', 'rename', 'renameat', 
                   'fopen', 'fopen64', 'fclose', 'socket', 'fcntl']
ALL_TYPES = ['datacall', 'directoryCall', 'ExtendedAttributesCall', 'MetadataCall', 'SpecialCall']
ALL_APPLICATIONS = ['gromacs', 'openfoam', 'pytorch', 'tensorflow']

N = 50
TIME_THRESHOLD = 30  # seconds

# Set up logging to capture ALL messages
def configure_logging(output_dir, debug_base):

    os.makedirs(output_dir, exist_ok=True)
    
    log_file = os.path.join(output_dir, 'autogluon_output.log')
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    # Configure file handler
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Configure stream handler for console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(message)s'))
    
    # Set levels
    file_handler.setLevel(logging.DEBUG)
    console_handler.setLevel(logging.INFO if not debug_base else logging.DEBUG)
    
    # Add handlers to root logger
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Special configuration for AutoGluon logger
    autogluon_logger = logging.getLogger('autogluon')
    autogluon_logger.setLevel(logging.DEBUG)
    autogluon_logger.propagate = True  # Ensure propagation to root logger



# Redirect stdout/stderr to logging
class StreamToLogger(object):
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        
    def write(self, buf):
        for line in buf.rstrip().splitlines():
            if line.strip():
                self.logger.log(self.log_level, line.rstrip())
                
    def flush(self):
        pass


def create_encoders():
    type_encoder = OneHotEncoder(categories=[ALL_TYPES], handle_unknown='ignore', sparse_output=False)
    application_encoder = OneHotEncoder(categories=[ALL_APPLICATIONS], handle_unknown='ignore', sparse_output=False)
    label_encoder = LabelEncoder()
    return type_encoder, application_encoder, label_encoder

