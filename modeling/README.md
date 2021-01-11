# Modeling Module

## Description
This module provides wrapper functions to train models, maake predictions, and evaluate NER and RD predictions based on data from struct files. For more information about the JSON struct format, please see the processing module.

## Usage

#### Summary
This module will aim to provide three basic actions:
1. Training: This action will take an annotated struct, a model type, and a task and will output a model folder.
2. Predict: This action will take a model folder and a struct and will return an a prediction-annotated struct.
3. Evaluate: This action will take struct containing both manual annotations and prediction-annotations and will provide a summary of the performance of the predictions.

### Task 1: Training
Training: This action will take an annotated struct, a model type, and a task and will output a model folder.

#### Arguments:
Command: ``train``

Positional: 
1. ``input_struct``: Path to input struct file.
2. ``model_dir``: Directory where trained model should be placed. 

Optional:
* ``--model``: Model architecture (bert, lstm).
* ``--task``: Task to be solved (ner, rd).
* ``--output_path``: Path of output struct. If not given, predictions will be stored in place.

Example: 
```bash
python <path-to-modeling-module>/cli.py <path-to-input-struct> <path-to-model_dir> --model=bert --task=ner
```
