#!/usr/bin/env bash
#SBATCH --job-name=onset_eval_small
#SBATCH -a 0-3%1
#SBATCH --gres=gpu:2
#SBATCH --partition=hcc
#SBATCH -c 32

source start_databases.sh
cd ..
start_db $selected_dataset

datasets=("dbpedia" "bto" "uniprot" "yago")

dataset_id=$(($SLURM_ARRAY_TASK_ID % 4))
# zeroshot=$(($SLURM_ARRAY_TASK_ID / 4))
cfg_idx=4
selected_dataset=${datasets[$dataset_id]}
echo "dataset_id: $dataset_id"
echo "selected_dataset: $selected_dataset"
# echo "zeroshot: $zeroshot"
echo "cfg_idx: $cfg_idx"


# if [ $zeroshot -eq 1 ]
# then
#     echo "Running zeroshot"
#     python query-eval.py --dataset $selected_dataset --cfg_idx $cfg_idx --zero_shot
# else
echo "Running normal"
python query-eval.py --dataset $selected_dataset --cfg_idx $cfg_idx
# fi
