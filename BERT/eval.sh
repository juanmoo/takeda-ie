gpu=0

#task: pos | ner
export TASK_NAME=ner
tagset=reaction

export TASK_DIR=/data/rsg/nlp/sibanez/00_MedTrialXtr/02_runs/00_NER/03_run_split_juan_80-20

#export MODEL_DIR=/data/rsg/chemistry/sibanez/01_chem_nlp/00_pretrained/chembert_v3.0/
export MODEL_DIR=$TASK_DIR

OUTPUT_DIR=$TASK_DIR
output_file="test.tags.preds"

n_epochs=3

CUDA_VISIBLE_DEVICES=${gpu} python3 run_tagging.py \
    --model_name_or_path ${MODEL_DIR} \
    --task_name $TASK_NAME \
    --tagset ${tagset} \
    --do_eval \
    --eval_on_test \
    --data_dir $TASK_DIR \
    --max_seq_length 512 \
    --per_gpu_eval_batch_size=8   \
    --per_gpu_train_batch_size=8   \
    --learning_rate 2e-5 \
    --num_train_epochs ${n_epochs} \
    --output_dir ${OUTPUT_DIR} \
    --write_outputs \
    --output_file ${output_file} \
    --overwrite_output_dir
    # --local_rank 2

# merge "test.pred"
test_file=${TASK_DIR}/test.txt
python3 compile_outputs.py \
    --test_file ${test_file} \
    --tag_file ${OUTPUT_DIR}/${output_file} \
    --output ${OUTPUT_DIR}/test.preds
echo "Compiled outputs to:", ${OUTPUT_DIR}/test.preds
