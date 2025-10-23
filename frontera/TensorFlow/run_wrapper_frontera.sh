#!/bin/bash

export SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]:-$0}" )" &> /dev/null && pwd )
HOME_DIR=$HOME
WORK_DIR=$WORK

export TRACE_TITLE="tracer"

# for slurm to use python correct version
module load intel/19.1.1 python3/3.9.2
module load cuda/11.3 boost/1.72 hwloc/1.11.13 nccl/2.9.9 cudnn/8.2.1 cmake/3.24.2
source $HOME_DIR/tf-venv/bin/activate

# script usage: bash run.sh <POSITION_OF_WORKER_IN_WRKS_ADDRS> <NUMBER_OF_THE_DESIRED_MODEL> <BATCH_SIZE> <N_EPOCHS> 
TASK_ID=$1
MODEL_NUMBER=$2
BATCH_SIZE=$3
N_EPOCHS=$4
DISTRIBUTION_STRATEGY=$5
DATASET=$6
POLICY=$7
if [ $POLICY == "hvac" ] ; then
        POLICY_CONFIG="_hvac"
fi
# OPTIMIZER=$5 -> a beatriz falou disto, mas nos scripts dela nunca usa...

SCRIPT_NAME=no_wait_wrapper_frontera.py
CONFIGS_FOLDER=$WORK_DIR/DistMonarch/configurations/deucalion

if [ $DATASET == "imagenet" ] ; then
        DATA_DIR="$WORK_DIR/imagenet/train"
        CONFIG_FILE=tf_placement_100g_disk_imagenet$POLICY_CONFIG.yaml # "tf_placement_100g_disk.yaml" "tf_placement_100g_disk_imagenet.yaml"
elif [ $DATASET == "openimages" ]; then
        DATA_DIR="$WORK_DIR/train"
        CONFIG_FILE=tf_placement_100g_disk$POLICY_CONFIG.yaml
else
        echo "ERROR CONDITION"
fi

export INSTALL_DIR=$WORK_DIR/DistMonarch/dependencies
export MONARCH_DIR=$WORK_DIR/DistMonarch/pastor/build
export MONARCH_CONFIGS_PATH=$CONFIGS_FOLDER/$CONFIG_FILE
export TASK_ID=$TASK_ID

rm -rf /tmp/openimages_tfrecords/
rm -rf /tmp/middleware_output

export PYTHONPATH=$PYTHONPATH:$WORK_DIR/ScriptVault/TFScripts/models/official-models-2.1.0

MODEL=""
echo $WRKS_ADDRS

if [ $MODEL_NUMBER == 0 ]
then
	MODEL="sns_vgg19.py"

elif [ $MODEL_NUMBER == 1 ]
then
        MODEL="sns_inceptionv3.py"

elif [ $MODEL_NUMBER == 2 ]
then
        MODEL="sns_shufflenet.py"

elif [ $MODEL_NUMBER == 3 ]
then
        MODEL="sns_resnet18.py"

elif [ $MODEL_NUMBER == 4 ]
then
        MODEL="sns_lenet.py"

elif [ $MODEL_NUMBER == 5 ]
then
        MODEL="sns_alexnet.py"

fi

if [ $DATASET == "imagenet" ] ; then
        MODEL="imagenet_$MODEL"
fi

LOG_PATH="/tmp/log_$TASK_ID.txt"

echo "About to run $pwd"

# Tracer
export DSTAT_PATH="$SCRIPT_DIR/../../../../../../dstat"

# Clean
if [ -d "$PROFILING_DIR" ]; then
    rm -rf "$PROFILING_DIR"/*
else
    mkdir -p "$PROFILING_DIR"
fi

mkdir -p $PROFILING_DIR/logs
touch $PROFILING_DIR/logs/srun_dstat_$(hostname).log
touch $PROFILING_DIR/logs/srun_nvidia_$(hostname).log

nohup python $DSTAT_PATH/dstat.py -tcdrnmg --ib --noheaders > $PROFILING_DIR/logs/srun_dstat_$(hostname).log 2>&1 &

{
        echo "timestamp [ms],temperature.gpu [%],utilization.gpu [%],utilization.memory [%],memory.total [MiB],memory.free [MiB],memory.used [MiB]"
        nvidia-smi --query-gpu=timestamp,temperature.gpu,utilization.gpu,utilization.memory,memory.total,memory.free,memory.used \
                --format=csv,nounits,noheader -l 1 | \
        awk -F", " -v OFS=", " "{
        split(\$1, dt, /[/ :.]/);
        epoch_sec = mktime(dt[1] \" \" dt[2] \" \" dt[3] \" \" dt[4] \" \" dt[5] \" \" dt[6]);
        timestamp_ms = epoch_sec * 1000 + dt[7];
        \$1 = timestamp_ms;
        print;
        fflush();
        }"
} > "$PROFILING_DIR/logs/srun_nvidia_$(hostname).log" 2>&1 &

sleep 300

#mkdir -p $SCRATCH/tst
LD_PRELOAD="$HOME/software/trace-collector/build/libtrace-collector.so" \
python $SCRIPT_NAME $MODEL $N_EPOCHS $BATCH_SIZE $DATA_DIR $TASK_ID $WRKS_ADDRS $DISTRIBUTION_STRATEGY #|& tee $LOG_PATH

sleep 300

unset LD_PRELOAD
deactivate

sh $SCRIPT_DIR/../../../../../../tracer/stabilize_traces.sh $PROFILING_DIR $SCRATCH/$TRACE_TITLE/$MODEL\_$N_EPOCHS\_$BATCH_SIZE\_$DATASET\_$(hostname)/
