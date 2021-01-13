'''
BERT NER Driver Module
'''
# Get file's directory to use bash scripts and relative imports.
import os
from re import sub
import sys
import json
from uuid import uuid4 as uuid
from tqdm import tqdm
from sklearn.metrics import f1_score, recall_score, precision_score

dir_path = os.path.dirname(os.path.realpath(__file__))
project_root = '/'.join(dir_path.split('/')[:-4])
sys.path.append(project_root)


# Imports
import subprocess
import tempfile

# Relative Imports
from processing import format

### Training ###

def train(struct_path, output_model_dir, **kwargs):

    struct = json.load(open(struct_path, 'r'))

    # Default GPU settings
    gpus = kwargs.get('gpus', "")

    tmp_dir = tempfile.TemporaryDirectory()

    # Create BIO annotation files
    kwargs['task'] = 'ner'
    bio_dict = format.struct_to_bio(struct, **kwargs)
    data_dir = os.path.join(tmp_dir.name, 'data_dir')
    os.makedirs(data_dir, exist_ok=True)
    data_dir_path = data_dir
    train_file_path = os.path.join(data_dir_path, 'train.txt')

    train_txts = []
    for doc_id in bio_dict:
        pars = bio_dict[doc_id]
        train_txts.extend(pars)

    with open(train_file_path, 'w') as bio_file:
        out = '\n\n'.join(train_txts)
        bio_file.write(out)

    # Train
    output_dir = os.path.join(tmp_dir.name, 'output_dir')
    os.makedirs(output_dir, exist_ok=True)
    output_dir_path = output_dir
    train_cmd = os.path.join(dir_path, 'BERT', 'train.sh')
    cmd = ['/bin/bash', train_cmd, data_dir_path, output_dir_path, gpus]
    print(' '.join(cmd))
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    stdout, _ = proc.communicate()

    cmd2 = ['mv', output_dir_path, output_model_dir]
    proc = subprocess.run(cmd2)


def pred(struct_path, model_dir, **kwargs):
    struct = json.load(open(struct_path, 'r'))

    # Default GPU settings
    gpus = kwargs.get('gpus', "")

    # Create Dataset
    tmp_dir = tempfile.TemporaryDirectory()
    data_dir = os.path.join(tmp_dir.name, 'data_dir')
    os.makedirs(data_dir, exist_ok=True)

    blank_txts = format.struct_to_bio_empty(struct)
    for doc_id in blank_txts:
        doc_dir = os.path.join(data_dir, doc_id)
        os.mkdir(doc_dir)

        test_file_path = os.path.join(doc_dir, 'test.txt')
        with open(test_file_path, 'w') as f:
            f.write(blank_txts[doc_id])

    # Get metadata to save along with predictions
    metadata = kwargs.get('metadata', None)
    if not metadata:
        metadata = dict()

    # Initialize NER Pred List if not existent
    if 'ner_preds' not in struct:
        struct['ner_preds'] = []
    if 'ner_evals' not in struct:
        struct['ner_evals'] = []
    if 'ner_metadata' not in struct:
        struct['ner_metadata'] = []

    ner_preds_dict = dict()

    # Make prediction per documents
    print('Making document predictions...')
    for doc_id in tqdm(blank_txts):
        doc_data_dir = os.path.join(data_dir, doc_id)
        doc_output_dir = doc_data_dir
        pred_cmd = os.path.join(dir_path, 'BERT', 'pred.sh')
        cmd = ['/bin/bash', pred_cmd, doc_data_dir, model_dir, doc_output_dir]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        proc.communicate()

        tags_path = os.path.join(doc_output_dir, 'test.tags.preds')
        doc_struct = struct['documents'][doc_id]

        with open(tags_path, 'r') as tags_file:
            lines = [l.strip() for l in tags_file.readlines()]
            pars_tags = []

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
                    pars_tags.append(lines[i:j])

                i = j

            # num paragraphs == num of paragraph preds
            assert(len(pars_tags) == len(
                struct['documents'][doc_id]['paragraphs']))

            ner_preds_dict[doc_id] = pars_tags
    
    struct['ner_preds'].append(ner_preds_dict)

    ## Evaluation ##

    # Get all ner annotations
    ner_annotations = []
    ner_predictions = []

    for doc_id in ner_preds_dict:
        doc_struct = struct['documents'][doc_id]

        for j, par in enumerate(doc_struct['paragraphs']):
            if ('annotated' in par) and par['annotated']:
                ner_annotations.extend(par['bio_annotations'])
                ner_predictions.extend(ner_preds_dict[doc_id][j])
            assert(len(ner_annotations) == len(ner_predictions))
    
    labels = list(set(ner_annotations) - {"O"})
    labels.sort(key=lambda s:s[::-1])

    if len(ner_annotations) > 0:
        pred_eval = {
            'precision': precision_score(ner_annotations, ner_predictions, average='micro', labels=labels),
            'recall': recall_score(ner_annotations, ner_predictions, average='micro', labels=labels),
            'f1': f1_score(ner_annotations, ner_predictions, average='micro', labels=labels),
        }
    else:
        pred_eval = {
            'error': 'No annotations available.'
        }

    struct['ner_metadata'].append(metadata)
    struct['ner_evals'].append(pred_eval)

    return struct


if __name__ == '__main__':
    import json
    output_model_dir = '/data/rsg/nlp/juanmoo1/projects/02_takeda_dev/00_takeda/tmp/model'
    struct_path = '/data/rsg/nlp/juanmoo1/projects/02_takeda_dev/00_takeda/tmp/changed.json'
    with open(struct_path, 'r') as f:
        struct = json.load(f)
        train(struct, output_model_dir)
