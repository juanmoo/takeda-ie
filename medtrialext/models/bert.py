'''
BERT Driver Module
'''

# Get file's directory to use bash scripts and relative imports.
from functools import reduce
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


# ============================= Training ============================= # 
def train(args):
    models_dir = args.models_dir
    ner_model_dir = os.path.join(models_dir, 'ner')
    rd_model_dir = os.path.join(models_dir, 'rd')

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


    cmd = ['/bin/bash', train_cmd, data_dir, output_dir, args.gpus, args.ner_num_epochs]
    cmd = [str(e) for e in cmd]

    print('Command Executed: \n{}'.format(cmd))

    proc = subprocess.Popen(cmd)
    proc.communicate()

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

    cmd = ['/bin/bash', train_cmd, data_dir, output_dir, args.gpus, args.rd_num_epochs]
    cmd = [str(e) for e in cmd]

    print('Command Executed: \n{}'.format(cmd))

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    stdout, _ = proc.communicate()

    cmd2 = ['mv', output_dir, args.rd_model_dir]
    subprocess.run(cmd2)


# ============================= Predicting ============================= # 
def predict(args):
    models_dir = args.models_dir
    ner_model_dir = os.path.join(models_dir, 'ner')
    rd_model_dir = os.path.join(models_dir, 'rd')

    args.ner_model_dir = ner_model_dir
    args.rd_model_dir = rd_model_dir

    if not 'output_struct_path' in vars(args):
        args.output_struct_path = args.input_struct

    # Make NER predictions
    if not args.skip_ner:
        pred_ner(args)

    if not args.skip_rd:
        pred_rd(args)

def pred_ner(args):
    print('Starting making NER preds ... ')

    # Load Input struct (result from ner pred)
    struct = None
    with open(args.input_struct, 'r') as struct_file:
        struct = json.load(struct_file)

    # Root Temp Dir
    tmp_dir = tempfile.TemporaryDirectory()

    # Create Dataset
    data_dir = os.path.join(tmp_dir.name, 'data_dir')
    os.makedirs(data_dir, exist_ok=True)
    ovr = vars(args).get('ner_or', 1)
    bio_dict = formatting.struct_to_bio_dict(args.input_struct, ovr, use_tags=False)
    for doc_id in bio_dict:
        doc_dir = os.path.join(data_dir, doc_id)
        os.makedirs(doc_dir, exist_ok=False)

        doc_file_path = os.path.join(doc_dir, 'test.txt')
        with open(doc_file_path, 'w') as doc_file:
            doc_file.write(bio_dict[doc_id])
    
    # Make prediction
    model_dir = args.ner_model_dir
    pred_cmd = os.path.join(dir_path, 'BERT_NER', 'pred.sh')

    for doc_id in tqdm(bio_dict):
        doc_data_dir = os.path.join(data_dir, doc_id)
        doc_output_dir = os.path.join(tmp_dir.name, 'output_dir')

        cmd = ['/bin/bash', pred_cmd, doc_data_dir, model_dir, doc_output_dir]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        proc.communicate()
    
        doc_tags_path = os.path.join(doc_output_dir, 'test.preds')
        with open(doc_tags_path, 'r') as tags_file:
            lines = [l.strip() for l in tags_file.readlines()]

            pars_toks = []
            pars_tags = []

            # Get all labels in documents
            i = 0
            while i < len(lines):
                # Skip any empty lines
                while i < len(lines) and lines[i] == '':
                    i += 1

                # find end of current par
                j = i
                while j < len(lines) and lines[j] != '':
                    j += 1
                if j > i:
                    ptoks = []
                    ptags = []
                    for l in lines[i:j]:
                        l = re.sub('\s+', ' ', l).strip()
                        l = l.split(' ')[:2]
                        l = l + (['O'] * (2 - len(l)))
                        tok, tag = l
                        ptags.append(tag)
                        ptoks.append(tok)

                    pars_tags.append(ptags)
                    pars_toks.append(ptoks)
                i = j

            # Get document labels
            doc_labs = list(reduce(lambda a,b: a + b, pars_tags))
            doc_labs = set([l[2:] for l in doc_labs if l[:2] in ['B-', 'I-']])

            # Store annotations
            count = 0
            for toks, tags in zip(pars_toks, pars_tags):
                txt = ' '.join(toks)

                for par in struct['documents'][doc_id]['paragraphs']:
                    if txt == par['text'].strip():
                        count += 1
                        if 'predictions' not in par:
                            par['predictions'] = {}
                        
                        if 'ner' not in par['predictions']:
                            par['predictions']['ner'] = {}
                        
                        spans = make_spans(tags, all_labels=doc_labs)
                        for k in spans:
                            if k not in par['predictions']['ner']:
                                par['predictions']['ner'][k] = []
                            par['predictions']['ner'][k].extend(spans[k])
                        
                        # Paragraphs are unique. There's no need to keep searching.
                        break
            print('Made predictions in {} paragraphs in {}.'.format(count, doc_id))

    # Save struct to new location and return struct
    with open(args.output_struct_path, 'w') as output_struct:
        json.dump(struct, output_struct, indent=4)

    return struct

def pred_rd(args):
    print('Starting making RD preds ... ')

    # Load Input struct
    struct = None
    with open(args.output_struct_path, 'r') as struct_file:
        struct = json.load(struct_file)

    # Root Temp Dir
    tmp_dir = tempfile.TemporaryDirectory()

    # Create Dataset
    data_dir = os.path.join(tmp_dir.name, 'data_dir')
    os.makedirs(data_dir, exist_ok=True)
    bio_dict = formatting.struct_to_bio_dict_rd(args.output_struct_path, is_pred=True)
    for doc_id in bio_dict:
        doc_dir = os.path.join(data_dir, doc_id)
        os.makedirs(doc_dir, exist_ok=False)

        doc_file_path = os.path.join(doc_dir, 'test.txt')

        with open(doc_file_path, 'w') as doc_file:
            doc_file.write(bio_dict[doc_id])
    
    # Make prediction
    model_dir = args.rd_model_dir
    pred_cmd = os.path.join(dir_path, 'BERT_RD', 'pred.sh')

    print('Starting making RD predictions ... ')
    for doc_id in tqdm(bio_dict):
        doc_data_dir = os.path.join(data_dir, doc_id)
        doc_output_dir = os.path.join(tmp_dir.name, 'output_dir')

        cmd = ['/bin/bash', pred_cmd, doc_data_dir, model_dir, doc_output_dir]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        proc.communicate()
    
        doc_tags_path = os.path.join(doc_output_dir, 'test.preds')
        with open(doc_tags_path, 'r') as tags_file:
            lines = [l.strip() for l in tags_file.readlines()]

            pars_toks = []
            pars_tags = []

            # Get all labels in documents
            i = 0
            while i < len(lines):
                # Skip any empty lines
                while i < len(lines) and lines[i] == '':
                    i += 1

                # find end of current par
                j = i
                while j < len(lines) and lines[j] != '':
                    j += 1
                if j > i:
                    ptoks = []
                    ptags = []
                    for l in lines[i:j]:
                        l = re.sub('\s+', ' ', l).strip()
                        l = l.split(' ')[:2]
                        l = l + (['O'] * (2 - len(l)))
                        tok, tag = l
                        ptags.append(tag)
                        ptoks.append(tok)

                    pars_tags.append(ptags)
                    pars_toks.append(ptoks)
                i = j

            # Get document labels
            doc_labs = list(reduce(lambda a,b: a + b, pars_tags))
            doc_labs = set([l[2:] for l in doc_labs if l[:2] in ['B-', 'I-']])
            doc_labs.add('arm_description')

            # Store annotations
            count = 0
            for toks, tags in zip(pars_toks, pars_tags):

                if ('[P1]' not in toks) or ('[P2]' not in toks):
                    continue

                # Remove delimiters 
                p1_idx = toks.index('[P1]')
                p2_idx = toks.index('[P2]')
                toks.pop(p2_idx)
                tags.pop(p2_idx)
                toks.pop(p1_idx)
                tags.pop(p1_idx)

                tags[p1_idx] = f'B-arm_description'
                for idx in range(p1_idx + 1, p2_idx - 1):
                    tags[idx] = f'I-arm_description'

                txt = ' '.join(toks)
                for par in struct['documents'][doc_id]['paragraphs']:
                    if txt == par['text'].strip():
                        count += 1

                        if 'predictions' not in par:
                            par['predictions'] = {}
                        
                        if 'rd' not in par['predictions']:
                            par['predictions']['rd'] = []
                        
                        # RD preds are conditional on arm_desc. Ensure to keep
                        # them together
                        spans = make_spans(tags, all_labels=doc_labs)
                        par['predictions']['rd'].append(spans)
                        
            print('Matched {} paragraphs in {}.'.format(count, doc_id))

    # Save struct to new location and return struct
    with open(args.output_struct_path, 'w') as output_struct:
        json.dump(struct, output_struct, indent=4)

    return struct


# ============================= Training ============================= # 
def make_spans(tags, all_labels=set()):
    labels = set() | all_labels

    spans = {k:[] for k in labels}

    i = 0
    while i < len(tags):
        # skip all irrelevant tags
        while i < len(tags) and tags[i][2:] not in labels:
            i += 1

        if i >= len(tags):
            break
        
        # Find end of span
        current_tag = tags[i][2:]
        assert(current_tag in spans)

        j = i + 1
        while j < len(tags) and tags[j].endswith(current_tag) and (not tags[j].startswith('B-')):
            j += 1
        spans[current_tag].append((i, j))

        i = j
    return spans