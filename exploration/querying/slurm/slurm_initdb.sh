#!/bin/bash
#SBATCH --job-name=onset_initdb
#SBATCH -c 1
#SBATCH --mem 8G
#SBATCH -a 0-4%2
#SBATCH --account=bkantz
#SBATCH --output=logs/init_%A_%a.out
#SBATCH --error=logs/init_%A_%a.err

datasets=("dbpedia" "bto" "uniprot" "yago")

selected_dataset=${datasets[$SLURM_ARRAY_TASK_ID]}
cd ..
source ../../backend/.venv/bin/activate

echo "Running init-db for dataset $SLURM_ARRAY_TASK_ID"
echo "Selected dataset: $selected_dataset"
python init-db.py --dataset $selected_dataset