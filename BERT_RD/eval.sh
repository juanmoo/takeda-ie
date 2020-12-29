gpu="0,1,2,3"

#task: pos | ner
export TASK_NAME=ner
tagset=takeda
export TASK_DIR="/data/rsg/nlp/juanmoo1/projects/02_takeda_dev/00_takeda/01_takeda_repo/data/v2_and_3/rd_split"
export MODEL_DIR=bert-base-cased
# export MODEL_DIR=$1

output_dir="/data/rsg/nlp/juanmoo1/projects/02_takeda_dev/00_takeda/01_takeda_repo/BERT_RD/output_dir"

n_epochs=3
output_file="test.tags.preds"

CUDA_VISIBLE_DEVICES=${gpu} python run_tagging.py \
    --model_name_or_path ${MODEL_DIR} \
    --task_name $TASK_NAME \
    --tagset ${tagset} \
    --do_eval \
    --eval_on_test \
    --data_dir $TASK_DIR \
    --max_seq_length 512 \
    --per_gpu_eval_batch_size=8   \
    --per_gpu_train_batch_size=8   \
    --learning_rate 2e-6 \
    --num_train_epochs ${n_epochs} \
    --output_dir ${output_dir} \
    --write_outputs \
    --output_file ${output_file} \
    --overwrite_output_dir
    # --local_rank 2

# merge "test.pred"
test_file=${TASK_DIR}/test.txt
python compile_outputs.py \
    --test_file ${test_file} \
    --tag_file ${output_dir}/${output_file} \
    --output ${output_dir}/test.preds
echo "Compiled outputs to:", ${output_dir}/test.preds

