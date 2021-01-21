'''
BERT Driver Module
'''

# Get file's directory to use bash scripts and relative imports.
import os
import re
import sys
import json
from tqdm import tqdm
import tempfile
import subprocess
from . import formatting

dir_path = os.path.dirname(os.path.realpath(__file__))
project_root = '/'.join(dir_path.split('/')[:-4])
sys.path.append(project_root)

def train(args):
    models_dir = args.models_dir
    ner_model_dir = os.path.join(models_dir, 'ner')
    rd_model_dir = os.path.join(models_dir, 'rd')
    os.makedirs(ner_model_dir, exist_ok=True)
    os.makedirs(rd_model_dir, exist_ok=True)

    args.ner_model_dir = ner_model_dir
    args.rd_model_dir = rd_model_dir

    # Train NER Model
    train_ner(args)

    # Train RD Model
    train_rd(args)

def train_ner(args):
    print('Starting NER training ...')

    # Root Temp Dir
    tmp_dir = tempfile.TemporaryDirectory()

    # Create Dataset
    data_dir = os.path.join(tmp_dir.name, 'data_dir')
    os.makedirs(data_dir, exist_ok=True)

    bio_dict = formatting.struct_to_bio_dict(args.input_struct, args.ner_or)
    train_text = '\n\n'.join(bio_dict.values())

    train_file_path = os.path.join(data_dir, 'train.txt')
    with open(train_file_path, 'w') as train_file:
        train_file.write(train_text)
    
    # Train
    output_dir = os.path.join(tmp_dir.name, 'output_dir')
    os.makedirs(output_dir, exist_ok=True)
    train_cmd = os.path.join(dir_path, 'BERT_NER', 'train.sh')

    # Veryfy args
    print('bash: {}'.format(os.path.isfile('/bin/bash')))
    print('train_cmd: {} | {}'.format(train_cmd, os.path.isfile(train_cmd)))
    print('data_dir: {} | {}'.format(data_dir, os.path.isdir(data_dir)))
    print('output_dir: {} | {}'.format(output_dir, os.path.isdir(output_dir)))

    cmd = ['/bin/bash', train_cmd, data_dir, output_dir, '\"' + args.gpus + '\"', args.ner_num_epochs]
    cmd = [str(e) for e in cmd]
    # cmd = ' '.join([str(e) for e in cmd])

    print('Command Executed: \n{}'.format(cmd))

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    stdout, _ = proc.communicate()

    cmd2 = ['mv', output_dir, args.ner_model_dir]
    subprocess.run(cmd2)


def train_rd(args):
    print('Starting RD training ...')

    # Root Temp Dir
    tmp_dir = tempfile.TemporaryDirectory()

    # Create Dataset
    data_dir = os.path.join(tmp_dir.name, 'data_dir')
    os.makedirs(data_dir, exist_ok=True)

    bio_dict = formatting.struct_to_bio_dict_rd(args.input_struct)
    train_text = '\n\n'.join(bio_dict.values())

    train_file_path = os.path.join(data_dir, 'train.txt')
    with open(train_file_path, 'w') as train_file:
        train_file.write(train_text)
    
    # Train
    output_dir = os.path.join(tmp_dir.name, 'output_dir')
    os.makedirs(output_dir, exist_ok=True)
    train_cmd = os.path.join(dir_path, 'BERT_RD', 'train.sh')

    # Veryfy args
    print('bash: {}'.format(os.path.isfile('/bin/bash')))
    print('train_cmd: {} | {}'.format(train_cmd, os.path.isfile(train_cmd)))
    print('data_dir: {} | {}'.format(data_dir, os.path.isdir(data_dir)))
    print('output_dir: {} | {}'.format(output_dir, os.path.isdir(output_dir)))

    cmd = ['/bin/bash', train_cmd, data_dir, output_dir, '\"' + args.gpus + '\"', args.ner_num_epochs]
    cmd = [str(e) for e in cmd]

    print('Command Executed: \n{}'.format(cmd))

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    stdout, _ = proc.communicate()

    cmd2 = ['mv', output_dir, args.rd_model_dir]
    subprocess.run(cmd2)