gpu="0,1,2,3,4,5,6,7"

#task: pos | ner
TASK_NAME=ner
tagset=takeda

DATA_DIR=$1
MODEL_DIR=$2
OUTPUT_DIR=$3
# TASK_DIR=$2

# export MODEL_DIR=$TASK_DIR
# OUTPUT_DIR=$TASK_DIR
output_file="test.tags.preds"
n_epochs=3 
 
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

CUDA_VISIBLE_DEVICES=${gpu} python ${DIR}/run_tagging.py \
    --model_name_or_path ${MODEL_DIR} \
    --task_name $TASK_NAME \
    --tagset ${tagset} \
    --do_eval \
    --data_dir $DATA_DIR\
    --max_seq_length 512 \
    --per_gpu_eval_batch_size=8   \
    --per_gpu_train_batch_size=8   \
    --learning_rate 2e-5 \
    --num_train_epochs ${n_epochs} \
    --output_dir ${OUTPUT_DIR} \
    --write_outputs \
    --output_file ${output_file} \
    --overwrite_output_dir \
    --eval_on_test
    
    # --freeze_bert \
    # --freeze_bert_embedding
    # --do_train \
    # --eval_on_test \
    # --local_rank 2

# merge "test.pred"
test_file=${DATA_DIR}/test.txt
python ${DIR}/compile_outputs.py \
    --test_file ${test_file} \
    --tag_file ${OUTPUT_DIR}/${output_file} \
    --output ${OUTPUT_DIR}/test.preds
echo "Compiled outputs to:", ${OUTPUT_DIR}/test.preds
