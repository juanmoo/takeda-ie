# Modeling Module

## Description
This module provides wrapper functions to train models, make predictions, and create a tabular summary of the predicted results. For more information about the JSON struct format, please see the [processing module](../processing/README.md).

## Usage

### Training
Training: This action will take an annotated struct, a model type, and a task and will output a model folder.

#### Arguments:
Command: ``train``

Positional: 
1. ``input_struct``: Path to input struct file.
2. ``model_dir``: Directory where trained model should be placed. 

Optional:
1. ``--model``: Model architecture (bert, lstm).
2. ``--task``: Task to be solved (ner, rd).
3. ``--oversampling_rate``: Oversampling rate to be used during training (default: 1).
4. ``--num_epochs``: Number of epochs to use during training (default: 10).

Example: 
```bash
python <path-to-modeling-module>/cli.py <path-to-input-struct> <path-to-model_dir> --model=bert --task=ner --oversampling_rate=5 --num_epochs=15
```

### Predict
Command: ``pred``

Positional:
1. ``input_struct``: Path to JSON struct file.
2. ``model_dir``: Path of model directory.

Optional:
1. ``--output_path``: By default, predictions are made in-place. If you'd like save predictions in a separate struct, specify a path using this flag.

Example:
```bash
python <path-to-modeling-module>/cli.py <path-to-input-struct> <path-to-model_dir> --output_path <path-to-output-struct>
```