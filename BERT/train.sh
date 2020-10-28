gpu=1

# task: pos | ner
export TASK_NAME=ner
tagset=reaction

#export TASK_DIR=/data/rsg/nlp/sibanez/00_MedTrialXtr/02_runs/00_NER/02_run_base_test_notab/
#model_dir: bert-base-cased, path_to_biobert, path_to_chembert
#export MODEL_DIR=/data/rsg/chemistry/sibanez/11_MedTrialExtractor/02_models/00_blueBERT/
export MODEL_DIR=bert-base-cased

OUTPUT_DIR=/data/rsg/nlp/juanmoo1/projects/02_takeda_dev/00_takeda/02_workdir_takeda/02_pilot/11_bert_output
TASK_DIR=$OUTPUT_DIR
DATA_DIR=/data/rsg/nlp/juanmoo1/projects/02_takeda_dev/00_takeda/02_workdir_takeda/02_pilot/10_data/oversampled

n_epochs=10

CUDA_VISIBLE_DEVICES=${gpu} python run_tagging.py \
    --model_name_or_path ${MODEL_DIR} \
    --task_name $TASK_NAME \
    --tagset ${tagset} \
    --do_train \
    --do_eval \
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
    # --freeze_bert \
    # --local_rank 2
