#!/bin/bash -e
#SBATCH -e OpenFOAM.err
#SBATCH -o OpenFOAM.out
#SBATCH -J openfoam
#SBATCH -n 192
#SBATCH -t 02:00:00
#SBATCH -p development
#SBATCH -N 4

module load openfoam
export LD_LIBRARY_PATH=/opt/apps/gcc/9.1.0/lib64:$LD_LIBRARY_PATH

# Export paths to dstat file and output dir
export DSTAT_PATH="$HOME/software/dstat.py"
export OUTPUT_DIR="$HOME/OpenFOAM/combustion/output"

# Cleans and creates output dir
if [ -d "$OUTPUT_DIR" ]; then
    rm -rf "$OUTPUT_DIR"/*
else
    mkdir -p "$OUTPUT_DIR"
fi
mkdir $OUTPUT_DIR/logs

# Go to tutorials path
cd $SCRATCH/My_OpenFOAM/9.0/run/tutorials/combustion/buoyantReactingFoam/Lagrangian/hotBoxes

# Clean tutorial directory
./Allclean

echo "Starting now" 

. $WM_PROJECT_DIR/bin/tools/RunFunctions

# Export path to Trace Collector
export LD_PRELOAD="$HOME/software/trace-collector/build/libtrace-collector.so"

# Start dstat on all nodes with nohup
srun --nodes=$SLURM_NNODES --ntasks-per-node=1 --exclusive \
    bash -c "nohup $PYTHON_PATH $DSTAT_PATH -tcdrnmg --ib --noheaders > $OUTPUT_DIR/logs/srun_dstat_\$(hostname).log 2>&1 &"

sleep 300

./Allrun-parallel

unset LD_PRELOAD

sleep 300

echo "End" 