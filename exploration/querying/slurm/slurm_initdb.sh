#!/bin/bash
#SBATCH --job-name=onset_initdb
#SBATCH -a 0-3%1
#SBATCH --gres=gpu:2
#SBATCH -c 32


datasets=("dbpedia" "bto" "uniprot" "yago")
selected_dataset=${datasets[$dataset_id]}
echo "SLURM_ARRAY_TASK_ID: $SLURM_ARRAY_TASK_ID"

source start_databases.sh
cd ..
start_db "$SLURM_ARRAY_TASK_ID"

echo "Running init-db for dataset $SLURM_ARRAY_TASK_ID"
python init-db.py --dataset "${selected_dataset}"

stop_db $SLURM_ARRAY_TASK_ID
