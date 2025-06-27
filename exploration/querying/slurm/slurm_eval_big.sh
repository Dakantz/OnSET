#!/bin/bash
#SBATCH --job-name=onset_eval_big
#SBATCH -c 1
#SBATCH --mem 11G
#SBATCH -a 0-4%2
#SBATCH --account=bkantz
#SBATCH --output=logs/eval_%A_%a.out
#SBATCH --error=logs/eval_%A_%a.err

cd ..
source ../../backend/.venv/bin/activate

datasets=("dbpedia" "bto" "uniprot" "yago")

dataset_id=$(($SLURM_ARRAY_TASK_ID % 4))
# zeroshot=$(($SLURM_ARRAY_TASK_ID / 4))
cfg_idx=3
selected_dataset=${datasets[$dataset_id]}
echo "dataset_id: $dataset_id"
echo "selected_dataset: $selected_dataset"
echo "zeroshot: $zeroshot"
echo "cfg_idx: $cfg_idx"

# if [ $zeroshot -eq 1 ]
# then
#     echo "Running zeroshot"
#     python query-eval.py --dataset $selected_dataset --cfg_idx $cfg_idx --zero_shot
# else
echo "Running normal"
python query-eval.py --dataset $selected_dataset --cfg_idx $cfg_idx
# fi
