#!/bin/bash
#SBATCH --job-name=onset_querygen
#SBATCH --cpus-per-task=32
#SBATCH -a 0-4%2
#SBATCH --gpus=4
#SBATCH --partition=ivc
#SBATCH --output=logs/init_%A_%a.out
#SBATCH --error=logs/init_%A_%a.err

source start_databases.sh

cd ..

start_db "$SLURM_ARRAY_TASK_ID"

echo "Running query generator for dataset $SLURM_ARRAY_TASK_ID"
python querygen.py --dataset "$SLURM_ARRAY_TASK_ID"

stop_db "$SLURM_ARRAY_TASK_ID"