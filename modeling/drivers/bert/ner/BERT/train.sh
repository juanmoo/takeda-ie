# gpu="0,1,2,3"

# task: pos | ner
export TASK_NAME=ner
tagset=takeda

export MODEL_DIR=bert-base-cased
DATA_DIR=$1
OUTPUT_DIR=$2
TASK_DIR=$OUTPUT_DIR
gpu=$3

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
n_epochs=10

CUDA_VISIBLE_DEVICES=${gpu} python ${DIR}/run_tagging.py \
    --model_name_or_path ${MODEL_DIR} \
    --task_name $TASK_NAME \
    --tagset ${tagset} \
    --do_train \
    --data_dir $DATA_DIR\
    --max_seq_length 512 \
    --per_gpu_eval_batch_size=8   \
    --per_gpu_train_batch_size=8   \
    --learning_rate 3e-5 \
    --num_train_epochs ${n_epochs} \
    --output_dir ${OUTPUT_DIR} \
    --overwrite_output_dir \
    --evaluate_during_training \
    --logging_steps 200 \
    --save_steps -1