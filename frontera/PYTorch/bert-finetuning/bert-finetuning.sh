#!/bin/bash

#SBATCH -J traces_path        # Job name
#SBATCH -o traces_path.o%j       # Name of stdout output file
#SBATCH -e traces_path.e%j       # Name of stderr error file
#SBATCH -p rtx           # Queue (partition) name
#SBATCH -N 4              # Total # of nodes (must be 1 for serial)
#SBATCH -t 05:00:00        # Run time (hh:mm:ss)

DATA_DIR="$SCRATCH/imagenet"
DATASET_DIR="$SCRATCH/datasets"
REPO_DIR_NAME="cola_public"
CHECKPOINTS_DIR="$SCRATCH/checkpoints"
# MOVIE_CONVERSATIONS="$DATASET_DIR/movie_conversations.txt"
# MOVIE_LINES="$DATASET_DIR/movie_lines.txt"
SCRIPT="$HOME/PyTorch/bert-finetuning/bert-finetuning.py"

module load gcc/9.1.0 
module load python3/3.9.2


# Activate the Python virtual environment
VENV_DIR="$SCRATCH/pytorch250"
VENV_PATH="$VENV_DIR/bin/activate"
if [ -f "$VENV_PATH" ]; then
    source "$VENV_PATH"
else
    echo "Error: Virtual environment not found at $VENV_PATH"
    
    python3 -m venv "$VENV_DIR"
    source "$VENV_PATH"
    
    # Copy library file only on initial creation
    cp /home1/apps/gcc/13.2.0/lib64/libstdc++.so.6 "$VENV_DIR/lib/"

    # install torch
    python3 -m pip install --upgrade pip
    python3 -m pip install torch==2.5.0 torchvision==0.20.0

    # Install necessary Python packages in the activated environment
    pip install transformers datasets tokenizers
    pip install urllib3==1.26.6
fi


#module load cuda/11.3

#export GLOO_SOCKET_IFNAME
#export NCCL_SOCKET_IFNAME=em1


# Check if the dataset files already exist
if [ ! -d "$DATASET_DIR/$REPO_DIR_NAME" ]; then
    echo "Dataset files not found. Downloading and extracting..."

    # Download the Cornell Movie Dialogs Corpus
    wget https://nyu-mll.github.io/CoLA/cola_public_1.1.zip

    # Unzip the downloaded file quietly
    unzip -qq cola_public_1.1.zip

    # Remove the zip file after extraction
    rm cola_public_1.1.zip

    # Create a datasets directory if it doesn't exist
    mkdir -p "$DATASET_DIR"
    mkdir -p "$CHECKPOINTS_DIR"

    # Move the relevant files to the datasets directory
    mv "$REPO_DIR_NAME" "$DATASET_DIR"

    # Optional: Clean up the extracted folder
    #rm -rf "cornell movie-dialogs corpus"
else
    echo "Dataset files already exist. Skipping download and extraction."
fi


nodes=($(scontrol -a show hostnames ${SLURM_JOB_NODELIST} | sort | uniq))
echo "Nodes: ${nodes[@]}"

#head_node_ip=$(hostname -s)-ib0
head_node_ip=$(hostname -s)

echo ib0ip $(ifconfig ib0 2> /dev/null | awk '/inet/{print $2}')

echo "Head node IP: $head_node_ip"

# Set environment variables for distributed training
export MASTER_ADDR=$head_node_ip
export MASTER_PORT=1234
export WORLD_SIZE=$SLURM_NTASKS
export RANK=$SLURM_PROCID
export LOCAL_RANK=$SLURM_LOCALID

echo "MASTER_ADDR: $MASTER_ADDR"
echo "MASTER_PORT: $MASTER_PORT"
echo "SLURM_RANK: $SLURM_PROCID"
echo "SLURM_LOCALID: $SLURM_LOCALID"

#export NCCL_DEBUG=INFO
#export GLOO_DEBUG=INFO

#export TORCH_DISTRIBUTED_DEBUG=DETAIL
export TORCHELASTIC_ENABLE_FILE_TIMER=1
export TORCHELASTIC_HEALTH_CHECK_PORT=$MASTER_PORT
#export LOGLEVEL=DEBUG


export LD_PRELOAD="$HOME/software/test/my/trace-collector/build/libpadll.so"
export DSTAT_PATH="$HOME/software/dstat.py"
export OUTPUT_DIR="output"

# Clean
if [ -d "$OUTPUT_DIR" ]; then
    rm -rf "$OUTPUT_DIR"/*
else
    mkdir -p "$OUTPUT_DIR"
fi
mkdir $OUTPUT_DIR/logs


# Start dstat on all nodes with nohup
srun --nodes=$SLURM_NNODES --ntasks-per-node=1 --exclusive \
    bash -c "nohup $PYTHON_PATH $DSTAT_PATH -tcdrnmg --ib --noheaders > $OUTPUT_DIR/logs/srun_dstat_\$(hostname).log 2>&1 &"

# Start nvidia-smi on all nodes with nohup
srun --nodes=$SLURM_NNODES --ntasks-per-node=1 --exclusive \
    bash -c '
        LOGFILE="$OUTPUT_DIR/logs/srun_nvidia_$(hostname).log"
        {
            echo "timestamp [ms],temperature.gpu [%],utilization.gpu [%],utilization.memory [%],memory.total [MiB],memory.free [MiB],memory.used [MiB]"
            nvidia-smi --query-gpu=timestamp,temperature.gpu,utilization.gpu,utilization.memory,memory.total,memory.free,memory.used \
                       --format=csv,nounits,noheader -l 1 | \
            awk -F", " -v OFS=", " '\''{
                split($1, dt, /[/ :.]/);
                epoch_sec = mktime(dt[1] " " dt[2] " " dt[3] " " dt[4] " " dt[5] " " dt[6]);
                timestamp_ms = epoch_sec * 1000 + dt[7];
                $1 = timestamp_ms;
                print;
                fflush();
            }'\'' 
        } > "$LOGFILE" 2>&1 &
    '


sleep 300


# LD_LIBRARY_PATH=$SCRATCH/pytorch250/lib/:$LD_LIBRARY_PATH LD_PRELOAD=$HOME/trace-collector/build/libpadll.so \
time srun --export=ALL \
torchrun \
	 --nnodes 4 \
	--nproc_per_node 4 \
	--rdzv_id $RANDOM \
	--rdzv_backend c10d \
	--rdzv_endpoint $MASTER_ADDR:$MASTER_PORT \
		$SCRIPT \
				--epochs 300 \
				--dataset $DATASET_DIR \
				--checkpoints $CHECKPOINTS_DIR


sleep 300

# Clean up
unset LD_PRELOAD
deactivate
# rm -rf "$VENV_DIR"

echo "End"