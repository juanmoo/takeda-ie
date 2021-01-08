gpu="0,2,3"
gpu=""

# task: pos | ner
export TASK_NAME=ner
tagset=takeda
#export TASK_DIR="/data/rsg/nlp/juanmoo1/projects/02_takeda_dev/00_takeda/02_workdir_takeda/02_pilot/10_data/v2_corrected_all/rd_bio/v3/x1"
export TASK_DIR=$1
export MODEL_DIR=bert-base-cased

#output_dir="/data/rsg/nlp/juanmoo1/projects/02_takeda_dev/00_takeda/02_workdir_takeda/02_pilot/14_bert_rd_output/x1"
output_dir=$2

n_epochs=20

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

CUDA_VISIBLE_DEVICES=${gpu} python ${DIR}/run_tagging.py \
    --model_name_or_path ${MODEL_DIR} \
    --task_name $TASK_NAME \
    --tagset ${tagset} \
    --do_train \
    --do_eval \
    --data_dir $TASK_DIR \
    --max_seq_length 512 \
    --per_gpu_eval_batch_size=8   \
    --per_gpu_train_batch_size=8   \
    --learning_rate 2e-6 \
    --num_train_epochs ${n_epochs} \
    --output_dir ${output_dir}/ \
    --overwrite_output_dir \
    --evaluate_during_training \
    --logging_steps 200 \
    --save_steps -1
    # --freeze_bert \
    # --local_rank 2

