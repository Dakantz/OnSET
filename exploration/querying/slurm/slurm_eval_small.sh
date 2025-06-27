#!/usr/bin/env bash
#SBATCH --job-name=onset_eval_small
#SBATCH -a 0-3%1
#SBATCH --gres=gpu:2
#SBATCH -c 32

datasets=("dbpedia" "bto" "uniprot" "yago")

dataset_id=$(($SLURM_ARRAY_TASK_ID % 4))
cfg_idx=4
selected_dataset=${datasets[$dataset_id]}
echo "dataset_id: $dataset_id"
echo "selected_dataset: $selected_dataset"
echo "cfg_idx: $cfg_idx"

source start_databases.sh
cd ..
start_db $selected_dataset

echo "Running normal"
python query-eval.py --dataset $selected_dataset --cfg_idx $cfg_idx

stop_db $selected_dataset