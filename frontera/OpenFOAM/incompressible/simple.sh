#!/bin/bash -e
#SBATCH -e OpenFOAM.err
#SBATCH -o OpenFOAM.out
#SBATCH -J openfoam
#SBATCH -n 192
#SBATCH -t 02:00:00
#SBATCH -p development
#SBATCH -N 4

module load openfoam
# source $FOAM_BASH
# module load gcc/9.1.0
export LD_LIBRARY_PATH=/opt/apps/gcc/9.1.0/lib64:$LD_LIBRARY_PATH
export DSTAT_PATH="$HOME/software/dstat.py"
export OUTPUT_DIR="$HOME/OpenFOAM/incompressible/output"


if [ -d "$OUTPUT_DIR" ]; then
    rm -rf "$OUTPUT_DIR"/*
else
    mkdir -p "$OUTPUT_DIR"
fi
mkdir $OUTPUT_DIR/logs


cd $SCRATCH/My_OpenFOAM/9.0/run/tutorials/incompressible/simpleFoam/drivaerFastback

# clean
# ./Allclean
rm -r *
cp -r $HOME/OpenFOAM/incompressible/drivaerFastback/* .
chmod +x Allrun

echo "Starting now" 

. $WM_PROJECT_DIR/bin/tools/RunFunctions


export LD_PRELOAD="$HOME/software/test/my/trace-collector/build/libpadll.so"

# Start dstat on all nodes with nohup
srun --nodes=$SLURM_NNODES --ntasks-per-node=1 --exclusive \
    bash -c "nohup $PYTHON_PATH $DSTAT_PATH -tcdrnmg --ib --noheaders > $OUTPUT_DIR/logs/srun_dstat_\$(hostname).log 2>&1 &"

sleep 300

./Allrun

unset LD_PRELOAD

sleep 300

echo "End" 