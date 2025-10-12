#!/bin/bash -e
#SBATCH -J gromacs
#SBATCH -o output/slurm.out
#SBATCH -e output/slurm.err
#SBATCH -N 4
#SBATCH -n 192
#SBATCH -p development
#SBATCH -t 02:00:00

# Load modules
module purge
module load gcc/9.1.0 impi/19.0.9 gromacs/2024

# Directory setup
export DSTAT_PATH="$HOME/software/dstat.py"
export OUTPUT_DIR="output"
export INPUT_DIR="input"


# Create clean output directory
rm -rf "$OUTPUT_DIR" || true
mkdir -p "$OUTPUT_DIR"
mkdir $OUTPUT_DIR/logs

# Export path to Trace Collector
export LD_PRELOAD="$HOME/software/test/my/trace-collector/build/libpadll.so"


# Start dstat on all nodes with nohup
srun --nodes=$SLURM_NNODES --ntasks-per-node=1 --exclusive \
    bash -c "nohup $PYTHON_PATH $DSTAT_PATH -tcdrnmg --ib --noheaders > $OUTPUT_DIR/logs/srun_dstat_\$(hostname).log 2>&1 &"

sleep 300

# ========== System Preparation ==========
# Create water box (uncomment if needed)
# gmx editconf \
#   -f "$INPUT_DIR/spc216.gro" \
#   -o "$INPUT_DIR/box.gro" \
#   -box 10 10 10 >> "$OUTPUT_DIR/editconf.log" 2>&1

# gmx solvate \
#   -cp "$INPUT_DIR/box.gro" \
#   -cs "$INPUT_DIR/spc216.gro" \
#   -o "$INPUT_DIR/initial_structure.gro" \
#   -p "$INPUT_DIR/topol.top" >> "$OUTPUT_DIR/solvate.log" 2>&1

# ========== Energy Minimization ==========
echo "Starting energy minimization..."
gmx grompp \
  -f "$INPUT_DIR/em.mdp" \
  -c "$INPUT_DIR/initial_structure.gro" \
  -p "$INPUT_DIR/topol.top" \
  -o "$OUTPUT_DIR/em.tpr" \
  >> "$OUTPUT_DIR/grompp_em.log" 2>&1

ibrun gmx_mpi mdrun -v \
  -s "$OUTPUT_DIR/em.tpr" \
  -o "$OUTPUT_DIR/em.trr" \
  -c "$OUTPUT_DIR/em.gro" \
  -g "$OUTPUT_DIR/em.log" \
  -e "$OUTPUT_DIR/em.edr" \
  >> "$OUTPUT_DIR/mdrun_em.log" 2>&1

# ========== NVT Equilibration ==========
echo "Starting NVT equilibration..."
gmx grompp \
  -f "$INPUT_DIR/nvt.mdp" \
  -c "$OUTPUT_DIR/em.gro" \
  -p "$INPUT_DIR/topol.top" \
  -o "$OUTPUT_DIR/nvt.tpr" \
  >> "$OUTPUT_DIR/grompp_nvt.log" 2>&1

ibrun gmx_mpi mdrun -v \
  -s "$OUTPUT_DIR/nvt.tpr" \
  -o "$OUTPUT_DIR/nvt.trr" \
  -c "$OUTPUT_DIR/nvt.gro" \
  -g "$OUTPUT_DIR/nvt.log" \
  -e "$OUTPUT_DIR/nvt.edr" \
  >> "$OUTPUT_DIR/mdrun_nvt.log" 2>&1

# ========== NPT Equilibration ==========
echo "Starting NPT equilibration..."
gmx grompp \
  -f "$INPUT_DIR/npt.mdp" \
  -c "$OUTPUT_DIR/nvt.gro" \
  -p "$INPUT_DIR/topol.top" \
  -o "$OUTPUT_DIR/npt.tpr" \
  >> "$OUTPUT_DIR/grompp_npt.log" 2>&1

ibrun gmx_mpi mdrun -v \
  -s "$OUTPUT_DIR/npt.tpr" \
  -o "$OUTPUT_DIR/npt.trr" \
  -c "$OUTPUT_DIR/npt.gro" \
  -g "$OUTPUT_DIR/npt.log" \
  -e "$OUTPUT_DIR/npt.edr" \
  >> "$OUTPUT_DIR/mdrun_npt.log" 2>&1

# ========== Production MD ==========
echo "Starting production MD..."
gmx grompp \
  -f "$INPUT_DIR/pme.mdp" \
  -c "$OUTPUT_DIR/npt.gro" \
  -p "$INPUT_DIR/topol.top" \
  -o "$OUTPUT_DIR/topol.tpr" \
  >> "$OUTPUT_DIR/grompp_prod.log" 2>&1

ibrun gmx_mpi mdrun -v \
  -s "$OUTPUT_DIR/topol.tpr" \
  -nsteps 2000000 \
  -dds 0.8 \
  -npme 32 \
  -o "$OUTPUT_DIR/traj.trr" \
  -g "$OUTPUT_DIR/md.log" \
  -e "$OUTPUT_DIR/ener.edr" \
  -c "$OUTPUT_DIR/final.gro" \
  >> "$OUTPUT_DIR/mdrun_prod.log" 2>&1

echo "Simulation completed successfully. Outputs in: $OUTPUT_DIR"

unset LD_PRELOAD

sleep 300

echo "End GROMACS"