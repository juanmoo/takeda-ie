gpu="0,1,2,3"

# task: pos | ner
export TASK_NAME=ner
tagset=takeda
export TASK_DIR="/data/rsg/nlp/juanmoo1/projects/02_takeda_dev/00_takeda/01_takeda_repo/data/v2_and_3/rd_split"
export MODEL_DIR=bert-base-cased

output_dir="/data/rsg/nlp/juanmoo1/projects/02_takeda_dev/00_takeda/01_takeda_repo/BERT_RD/output_dir"

n_epochs=2

CUDA_VISIBLE_DEVICES=${gpu} python run_tagging.py \
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

