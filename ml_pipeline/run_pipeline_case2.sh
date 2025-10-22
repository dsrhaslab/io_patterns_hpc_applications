#!/bin/bash
#SBATCH --error=output/ml.err
#SBATCH --output=output/ml.out
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
CASE="1536"
RUN="3"
NUM="1"
SITUATION="only"
DEBUG="--debug"

# Construct output directory
OUTPUT_DIR="output_results_${APPLICATION}_${CASE}_${RUN}_next${NUM}_${SITUATION}"

export OPENBLAS_NUM_THREADS=1

# Run the pipeline with the output directory
python pipeline_case2.py \
   --application "$APPLICATION" \
   --case "$CASE" \
   --run "$RUN" \
   --situation "$SITUATION" \
   --num_predictions "$NUM" \
   --output "$OUTPUT_DIR" \
   $DEBUG
