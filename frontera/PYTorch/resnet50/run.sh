#!/bin/bash

#SBATCH -J eth           # Job name
#SBATCH -o eth_tr.o%j       # Name of stdout output file
#SBATCH -e eth_tr.e%j       # Name of stderr error file
#SBATCH -p rtx           # Queue (partition) name
#SBATCH -N 4              # Total # of nodes (must be 1 for serial)
#SBATCH -t 02:00:00        # Run time (hh:mm:ss)

DATA_DIR="$SCRATCH/imagenet_data/imagenet"
VENV_DIR="$SCRATCH/kaggle_venv"
SCRIPT="$HOME/PyTorch/imagenet/main_simple_ult.py"

# Create fresh virtual environment
if [ ! -d "$VENV_DIR" ]; then
     echo "Creating new virtual environment..." | tee -a eth_tr.o%j

     module load python3/3.9.2
     
     python3 -m venv "$VENV_DIR"
     source "$VENV_DIR/bin/activate"
    
     # Copy library file only on initial creation
     cp /home1/apps/gcc/13.2.0/lib64/libstdc++.so.6 "$VENV_DIR/lib/"

     # install torch
     python3 -m pip install --upgrade pip
     python3 -m pip install torch==2.5.0 torchvision==0.20.0
else
    echo "Using existing virtual environment..." | tee -a eth_tr.o%j
    source "$VENV_DIR/bin/activate"
fi

module load gcc/9.1.0 python3/3.9.2
module load cuda/11.3

export NCCL_SOCKET_IFNAME=ib0

nodes=($(scontrol -a show hostnames ${SLURM_JOB_NODELIST} | sort | uniq))
echo "Nodes: ${nodes[@]}" | tee -a eth_tr.o%j

head_node_ip=$(hostname -s)
echo "Head node IP: $head_node_ip" | tee -a eth_tr.o%j

# Set environment variables for distributed training
export MASTER_ADDR=$head_node_ip
export MASTER_PORT=1234
export WORLD_SIZE=$SLURM_NTASKS
export RANK=$SLURM_PROCID
export LOCAL_RANK=$SLURM_LOCALID

echo "MASTER_ADDR: $MASTER_ADDR" | tee -a eth_tr.o%j
echo "MASTER_PORT: $MASTER_PORT" | tee -a eth_tr.o%j
echo "SLURM_RANK: $SLURM_PROCID" | tee -a eth_tr.o%j
echo "SLURM_LOCALID: $SLURM_LOCALID" | tee -a eth_tr.o%j

export TORCHELASTIC_ENABLE_FILE_TIMER=1
export TORCHELASTIC_HEALTH_CHECK_PORT=$MASTER_PORT

export LD_LIBRARY_PATH="$VENV_DIR/lib:$LD_LIBRARY_PATH"
export LD_PRELOAD="$HOME/software/test/my/trace-collector/build/libpadll.so"
export DSTAT_PATH="$HOME/software/dstat.py"
export OUTPUT_DIR="output"

# Clean
echo "Cleaning up old files..." | tee -a eth_tr.o%j
rm -f check* eth*

if [ -d "$OUTPUT_DIR" ]; then
    echo "Removing old output files..." | tee -a eth_tr.o%j
    rm -rf "$OUTPUT_DIR"/*
else
    echo "Creating output directory..." | tee -a eth_tr.o%j
    mkdir -p "$OUTPUT_DIR"
fi
mkdir $OUTPUT_DIR/logs

# Start dstat on all nodes with nohup
echo "Starting dstat..." | tee -a eth_tr.o%j
srun --nodes=$SLURM_NNODES --ntasks-per-node=1 --exclusive \
    bash -c "nohup $PYTHON_PATH $DSTAT_PATH -tcdrnmg --ib --noheaders > $OUTPUT_DIR/logs/srun_dstat_\$(hostname).log 2>&1 &"

# Start nvidia-smi on all nodes
echo "Starting nvidia-smi..." | tee -a eth_tr.o%j
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

echo "Starting distributed training..." | tee -a eth_tr.o%j
srun --export=ALL \
torchrun \
--nnodes 4 \
--nproc_per_node 4 \
--rdzv_id $RANDOM \
--rdzv_backend c10d \
--rdzv_endpoint $MASTER_ADDR:$MASTER_PORT \
     $SCRIPT \
                --epochs 2 --save_every 1 --batch_size 128 --dist true --model resnet50 --enable_log false $DATA_DIR

sleep 300

# Clean up
echo "Cleaning up environment..." | tee -a eth_tr.o%j
unset LD_PRELOAD
deactivate
# rm -rf "$VENV_DIR"

echo "End of script." | tee -a eth_tr.o%j
