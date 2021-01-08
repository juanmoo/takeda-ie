'''
Main entry point to use modeling CLI.
'''

import os
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

    # gpus
    gpus = ','.join([str(j) for j in range(args.gpu_count)])

    kwargs = vars(args)
    kwargs['struct'] = input_struct
    kwargs['output_model_dir'] = model_dir
    kwargs['gpus'] = gpus

    train_func(**kwargs)


if __name__ == '__main__':
    # Main Parser
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='sub-command help')
    # Main Optional Arguments
    parser.add_argument('--gpu_count', type=int, default=0)

    # Train Parser
    train_parser = subparsers.add_parser('train', help='Parse GROBID XMLs')
    train_parser.add_argument('input_struct', type=str,
                            help='Path to JSON struct file.')
    train_parser.add_argument('model_dir', type=str,
                            help='Path of model directory')
    train_parser.add_argument('--model', type=str, default='bert', help='Model architecture (bert,)')
    train_parser.add_argument('--task', type=str, default='ner', help='Task (ner, )')

    train_parser.set_defaults(handler=train_cli)


    args = parser.parse_args()

    # Execute handler function
    args.handler(args)
