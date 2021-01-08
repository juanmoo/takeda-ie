gpu=3

#task: pos | ner
export TASK_NAME=ner
tagset=reaction

base_dir=/data/rsg/chemistry/sibanez/01_chem_nlp/19_chemu_FINAL/01_runs/08_run_05_NER_TEST_ALL_10

export MODEL_DIR=${base_dir}/01_model_dir
export TEST_DIR=${base_dir}/02_task_dir
export OUTPUT_DIR=${base_dir}/03_output_dir
export DATA_DIR=${base_dir}/04_data_dir
export CACHED_DATA_DIR=${base_dir}/05_cached_data_dir

#output_file="test.tags.preds"

n_epochs=3

CUDA_VISIBLE_DEVICES=${gpu} python3 -m pdb run_tagging_dir.py \
    --model_name_or_path ${MODEL_DIR} \
    --task_name $TASK_NAME \
    --tagset ${tagset} \
    --test_dir $TEST_DIR \
    --data_dir $DATA_DIR \
    --cached_data_dir $CACHED_DATA_DIR \
    --do_eval \
    --eval_on_test \
    --max_seq_length 512 \
    --per_gpu_eval_batch_size=8   \
    --per_gpu_train_batch_size=8   \
    --learning_rate 2e-5 \
    --num_train_epochs ${n_epochs} \
    --output_dir ${OUTPUT_DIR} \
    --write_outputs \
    --overwrite_output_dir
     
    #--local_rank 2
    #--output_file ${output_file} \
