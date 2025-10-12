#!/bin/bash
#SBATCH -J dist-monarch       # Job name
#SBATCH -o vanilla_imagenet_resnet18_4e_8nodes_p.out%j   # Name of stdout output file
#SBATCH -e vanilla_imagenet_resnet18_4e_8nodes_p.err%j   # Name of stderr error file
#SBATCH -N 8                  # Total # of nodes (must be 1 for serial)
#SBATCH -n 8                  # Total # of mpi tasks (should be 1 for serial)
#SBATCH -t 02:00:00           # Run time (hh:mm:ss)
#SBATCH -p rtx

# RUN THIS THROUGH sh ./sbatch_frontera.sh

SINGLE_JOB_SCRIPT_NAME=run_wrapper_frontera.sh
NODE_LOCAL_STORAGE="/tmp"

export WRKS_ADDRS=$(./get_ips_frontera.sh)
echo ${WRKS_ADDRS}
nodes=($(scontrol show hostnames ${SLURM_JOB_NODELIST} | sort | uniq ))
numnodes=${#nodes[@]}
last=$(( $numnodes - 1 ))

MODEL_ID=3 #0-vgg19, 1-incenptionv3, 2-shufflenet não dá com 128, 3-resnet18, 4-lenet, 5-alexnet
BATCH_SIZE=64
N_EPOCHS=4 # 6 for case 5
DISTRIBUTION_STRATEGY="multi_worker_mirrored" # "one_device" "multi_worker_mirrored", "parameter_server", "mirrored"
DATASET="imagenet" # "imagenet" "openimages"
POLICY="distmonarch" # "hvac" "distmonarch" - none for case 5
PROFILING="true" # "true" "false" - false for case 5
DEBUG="false" # "true" "false"
TEST_TITLE=$MODEL_ID\_$N_EPOCHS\_$BATCH_SIZE\_$DATASET\_dist

for i in $(seq 0 $last )
do
        ssh $(getent hosts ${nodes[$i]} | awk '{print $2}' | head -1) \
        """export WRKS_ADDRS=$WRKS_ADDRS;
        export PROFILING_DIR=$PROFILING_DIR;
        export HOME_DIR=$HOME;
        export WORK_DIR=$WORK;
        export TEST_TITLE=$TEST_TITLE;
        export NODE_LOCAL_STORAGE="/tmp";
        export MACHINE="frontera";
        cd ${SCRIPT_DIR}; ./${SINGLE_JOB_SCRIPT_NAME} ${i} ${MODEL_ID} ${BATCH_SIZE} ${N_EPOCHS} ${DISTRIBUTION_STRATEGY} ${DATASET} ${POLICY} ${PROFILING} ${DEBUG}""" &
        pids[${i}]=$!
done
# wait for all processes to finish
for pid in ${pids[*]}
do 
        wait $pid 
done

echo "Finished multi_run_wrapper_frontera.sh"
