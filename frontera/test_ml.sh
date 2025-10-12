#!/bin/bash -e
#SBATCH -e SCRIPT.err
#SBATCH -o SCRIPT.out
#SBATCH -J test_ml
#SBATCH -t 02:00:00
#SBATCH -p development
#SBATCH -N 1

python3 ../test_ml.py --app gromacs -d