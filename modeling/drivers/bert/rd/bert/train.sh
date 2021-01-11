
# task: pos | ner
export TASK_NAME=ner
export tagset=takeda
#export TASK_DIR="/data/rsg/nlp/juanmoo1/projects/02_takeda_dev/00_takeda/02_workdir_takeda/02_pilot/10_data/v2_corrected_all/rd_bio/v3/x1"

export DATA_DIR=${1}
export OUTPUT_DIR=${2}
export gpu=${3}

export MODEL_DIR=bert-base-cased
n_epochs=20

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

CUDA_VISIBLE_DEVICES=${gpu} python ${DIR}/run_tagging.py \
    --model_name_or_path ${MODEL_DIR} \
    --task_name $TASK_NAME \
    --tagset ${tagset} \
    --do_train \
    --data_dir $DATA_DIR \
    --max_seq_length 512 \
    --per_gpu_eval_batch_size=8   \
    --per_gpu_train_batch_size=8   \
    --learning_rate 2e-6 \
    --num_train_epochs ${n_epochs} \
    --output_dir ${OUTPUT_DIR}/ \
    --overwrite_output_dir \
    --logging_steps 200 \
    --save_steps -1
