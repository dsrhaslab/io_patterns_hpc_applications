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
NUM="10"
SITUATION="only"
DEBUG="--debug"
MODEL_TO_LOAD="ag-20250607_191856"
WARM_UP_TIME=450

# Construct output directory
OUTPUT_DIR="output_results_${APPLICATION}_${CASE}_${RUN}_next${NUM}_${SITUATION}"

export OPENBLAS_NUM_THREADS=1

python start_from_load_model_pipeline_case2.py \
    --application "$APPLICATION" \
    --case "$CASE" \
    --run "$RUN" \
    --situation "$SITUATION" \
    --num_predictions "$NUM" \
    --model "$MODEL_TO_LOAD" \
    --warm_up "$WARM_UP_TIME" \
    --output "$OUTPUT_DIR" \
    $DEBUG
