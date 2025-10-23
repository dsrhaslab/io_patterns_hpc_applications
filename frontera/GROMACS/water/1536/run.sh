#!/bin/bash -e
#SBATCH -e GROMACS.err
#SBATCH -o GROMACS.out
#SBATCH -J gromacs
#SBATCH -n 192
#SBATCH -t 02:00:00
#SBATCH -p development
#SBATCH -N 4

module load gcc/9.1.0
module load impi/19.0.9
module load gromacs/2024

# Export paths to dstat file and output dir
export DSTAT_PATH="$HOME/software/dstat.py"
export OUTPUT_DIR="output"

# Cleans and creates output dir
if [ -d "$OUTPUT_DIR" ]; then
    rm -rf "$OUTPUT_DIR"/*
else
    mkdir -p "$OUTPUT_DIR"
fi
mkdir $OUTPUT_DIR/logs


# Start dstat on all nodes with nohup
srun --nodes=$SLURM_NNODES --ntasks-per-node=1 --exclusive \
    bash -c "nohup $PYTHON_PATH $DSTAT_PATH -tcdrnmg --ib --noheaders > $OUTPUT_DIR/logs/srun_dstat_\$(hostname).log 2>&1 &"

sleep 300

# Prepare the input files
gmx grompp -f pme.mdp -o $OUTPUT_DIR/topol.tpr >> $OUTPUT_DIR/grompp.log 2>&1

# Debugging and job environment
env >> $OUTPUT_DIR/env.log
echo $SLURM_NTASKS >> $OUTPUT_DIR/env.log

echo "Starting now" >> $OUTPUT_DIR/env.log

# Export path to Trace Collector
export LD_PRELOAD="$HOME/software/trace-collector/build/libtrace-collector.so"

# Run the simulation
ibrun gmx_mpi mdrun -v \
    -s $OUTPUT_DIR/topol.tpr \
    -nsteps 100000 \
    -resethway \
    -dd 12 4 4\
    -o $OUTPUT_DIR/mdrun.trr \
    -g $OUTPUT_DIR/mdrun.log \
    -e $OUTPUT_DIR/mdrun.edr \
    -c $OUTPUT_DIR/mdrun.gro \
    >> $OUTPUT_DIR/mdrun_output.log 2>&1

unset LD_PRELOAD

sleep 300


echo "End GROMACS"