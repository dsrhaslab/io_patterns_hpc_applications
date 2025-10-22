#!/bin/bash
#SBATCH --error=output/ml_case1.err
#SBATCH --output=output/ml_case1.out
#SBATCH --job-name "ML"
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --ntasks=1
#SBATCH --time 04:00:00
#SBATCH --partition=normal-a100-40
#SBATCH --account=i20240002g
#SBATCH -D .

source ../ml/ml_env/bin/activate

# pip install seaborn
# pip install tsfresh

# Set variables
APPLICATION="gromacs"
CASE="md_cluster_workflow"
RUN="3"
# NUM="100"
# SITUATION="app"
DEBUG="--debug"

# Construct output directory
OUTPUT_DIR="output_results_${APPLICATION}_${CASE}_${RUN}_pipeline1"

export OPENBLAS_NUM_THREADS=1

# Run the pipeline with the output directory
python pipeline_case1.py \
   --application "$APPLICATION" \
   --case "$CASE" \
   --run "$RUN" \
   --output "$OUTPUT_DIR" \
   $DEBUG
