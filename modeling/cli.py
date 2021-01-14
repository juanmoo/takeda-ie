'''
Main entry point to use modeling CLI.
'''

import os
import json
import argparse
import drivers

# Train CLI wrapper


def train_cli(args):
    # Normalize Paths
    input_struct = os.path.normpath(args.input_struct)
    input_struct = os.path.realpath(input_struct)

    model_dir = os.path.normpath(args.model_dir)
    model_dir = os.path.realpath(model_dir)

    kwargs = vars(args)
    kwargs['input_struct'] = input_struct
    kwargs['model_dir'] = model_dir

    model = args.model
    task = args.task

    train_func = None
    if model == 'bert':
        if task == 'ner':
            train_func = drivers.bert.ner.train
        elif task == 'rd':
            train_func = drivers.bert.rd.train

    # gpus
    gpus = ','.join([str(j) for j in range(args.gpu_count)])

    kwargs = vars(args)
    kwargs['struct_path'] = input_struct
    kwargs['output_model_dir'] = model_dir
    kwargs['gpus'] = gpus

    train_func(**kwargs)

    # Save Model metadata along w/ model
    assert(os.path.isdir(model_dir))
    metadata = {
        'architecture': model,
        'task': task,
    }
    metadata_file = os.path.join(model_dir, 'metadata.json')
    with open(metadata_file, 'w') as md_file:
        json.dump(metadata, md_file, indent=4)


def pred_cli(args):
    # Normalize Paths
    input_struct = os.path.normpath(args.input_struct)
    input_struct = os.path.realpath(input_struct)

    model_dir = os.path.normpath(args.model_dir)
    model_dir = os.path.realpath(model_dir)

    kwargs = vars(args)
    kwargs['struct_path'] = input_struct
    kwargs['model_dir'] = model_dir

    # Get model metadata
    metadata_path = os.path.join(model_dir, 'metadata.json')
    metadata = None
    with open(metadata_path, 'r') as md_file:
        metadata = json.load(md_file)
    metadata['model_dir'] = model_dir

    model = metadata['architecture']
    task = metadata['task']
    kwargs['model'] = model
    kwargs['task'] = task
    kwargs['metadata'] = metadata


    pred_func = None
    if model == 'bert':
        if task == 'ner':
            pred_func = drivers.bert.ner.pred
        elif task == 'rd':
            pred_func = drivers.bert.rd.pred
        else:
            raise Exception('Unknown/unsuported architecture')
    elif model == 'lstm':
        raise Exception('Unknown/unsupported architecture')
    
    # gpus
    gpus = ','.join([str(j) for j in range(args.gpu_count)])
    kwargs['gpus'] = gpus

    new_struct = pred_func(**kwargs)
    
    if 'output_path' in kwargs:
        out_struct_path = kwargs['output_path']
    else:
        out_struct_path = input_struct
    
    with open(out_struct_path, 'w') as f:
        json.dump(new_struct, f)


if __name__ == '__main__':
    # Main Parser
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='sub-command help')
    # Main Optional Arguments
    parser.add_argument('--gpu_count', type=int, default=0)

    # Train Parser
    train_parser = subparsers.add_parser('train', help='Train model')
    train_parser.add_argument('input_struct', type=str,
                              help='Path to JSON struct file.')
    train_parser.add_argument('model_dir', type=str,
                              help='Path of model directory')
    train_parser.add_argument(
        '--model', type=str, default='bert', help='Model architecture (bert,)')
    train_parser.add_argument(
        '--task', type=str, default='ner', help='Task (ner, rd)')
    train_parser.add_argument('--oversample_rate', type=int, default=1, help='Oversampling rate to be used during training.')
    train_parser.set_defaults(handler=train_cli)

    # Pred Parser
    pred_parser = subparsers.add_parser(
        'pred', help='Make prediction using existing model.')
    pred_parser.add_argument('input_struct', type=str,
                             help='Path to JSON struct file')
    pred_parser.add_argument('model_dir', type=str,
                             help='Path of model directory')
    pred_parser.add_argument('--output_path', type=str,
                             help='By default, predictions are made in-place. If you\'d like to save predictions in a separate struct, specify a path using this flag.')
    pred_parser.set_defaults(handler=pred_cli)

    args = parser.parse_args()

    # Execute handler function
    args.handler(args)
