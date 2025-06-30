#!/bin/bash
#SBATCH --job-name=onset_initdb
#SBATCH -a 0-3%1
#SBATCH --gres=gpu:2
#SBATCH -c 32
#SBATCH --partition=ivc
#SBATCH --output=logs/init_%A_%a.out
#SBATCH --error=logs/init_%A_%a.err

source ~/.zshrc

conda activate onset-env

source ../../../backend/.venv/bin/activate

datasets=("dbpedia" "bto" "uniprot" "yago")
dataset_id=$(($SLURM_ARRAY_TASK_ID % 4))
selected_dataset=${datasets[$dataset_id]}
echo "SLURM_ARRAY_TASK_ID: $SLURM_ARRAY_TASK_ID"

source start_databases.sh
cd ..
start_db "$selected_dataset"

echo "Running init-db for dataset $selected_dataset"




python init-db.py --dataset "${selected_dataset}"

stop_db $SLURM_ARRAY_TASK_ID
