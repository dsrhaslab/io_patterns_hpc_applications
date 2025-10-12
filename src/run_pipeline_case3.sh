#!/bin/bash
#SBATCH --error=output/ml_case3.err
#SBATCH --output=output/ml_case3.out
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
APPLICATION="openfoam"
CASE="incompressible"
RUN="1"
SITUATION="only"
DEBUG="--debug"

# Construct output directory
OUTPUT_DIR="output_results_brust_${APPLICATION}_${CASE}_${RUN}_${SITUATION}_30"

export OPENBLAS_NUM_THREADS=1
export TERM=dumb


# Run the pipeline with the output directory
python pipeline_case3.py \
   --application "$APPLICATION" \
   --case "$CASE" \
   --run "$RUN" \
   --situation "$SITUATION" \
   --output "$OUTPUT_DIR" \
   $DEBUG