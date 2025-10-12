import socket
import os
import time
import sys
import threading
import subprocess

PORT = 50053
MAX_CONNECTIONS = 100
DATASET_DIR = ""
EPOCHS = 0
BATCH_SIZE = 0
TASK_ID = 0
MODEL = ""
N_WORKERS = 0
DISTRIBUTION_STRATEGY = "one_device"
WRKS_ADDRS = ""
WRKS_LIST = []

def main():
    global DATASET_DIR, EPOCHS, BATCH_SIZE, TASK_ID, MODEL, DISTRIBUTION_STRATEGY, WRKS_ADDRS, WRKS_LIST
    #N_WORKERS = len(workers) - 1 # we don't want to receive or send messages to ourselves
    MODEL = sys.argv[1]
    EPOCHS = int(sys.argv[2])
    BATCH_SIZE = int(sys.argv[3])
    DATASET_DIR = sys.argv[4]
    TASK_ID = int(sys.argv[5])
    if len(sys.argv) >= 7:
        WRKS_LIST  = sys.argv[6].split(",")
        WRKS_ADDRS = ":7555,".join(WRKS_LIST) + ":7555"
        if len(sys.argv) >= 8:
            DISTRIBUTION_STRATEGY = sys.argv[7]
    print(f"Wrapper: Starting training with {len(WRKS_LIST)*4} GPUs")
    command = f'python {MODEL} --distribution_strategy={DISTRIBUTION_STRATEGY} --worker_hosts={WRKS_ADDRS} --skip_eval --train_epochs={EPOCHS} --batch_size={BATCH_SIZE} --model_dir="/tmp/checkpointing" --data_dir={DATASET_DIR} --task_index={TASK_ID} --num_gpus={4*len(WRKS_LIST)}'
    subprocess.run(command, shell=True, check=True)

if __name__ == "__main__":
    main()