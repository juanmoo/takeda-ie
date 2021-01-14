'''
BERT NER Driver Module
'''
# Get file's directory to use bash scripts and relative imports.
from functools import reduce
import os
from re import sub
import re
import sys
import json
from uuid import uuid4 as uuid
from tqdm import tqdm
from sklearn.metrics import f1_score, recall_score, precision_score
from sklearn.metrics import confusion_matrix

dir_path = os.path.dirname(os.path.realpath(__file__))
project_root = '/'.join(dir_path.split('/')[:-4])
sys.path.append(project_root)

# Imports
import subprocess
import tempfile

# Relative Imports
from processing import format

### Training ###

def train(input_struct, model_dir, **kwargs):

    struct = json.load(open(input_struct, 'r'))

    # Default GPU settings
    gpus = kwargs.get('gpus', "0,1,2,3,4,5,6,7")

    tmp_dir = tempfile.TemporaryDirectory()

    # Create BIO annotation files
    kwargs['task'] = 'rd'
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
    output_dir = os.path.join(tmp_dir.name, 'model_dir')
    os.makedirs(output_dir, exist_ok=True)
    output_dir_path = output_dir
    train_cmd = os.path.join(dir_path, 'BERT', 'train.sh')
    cmd = ['/bin/bash', train_cmd, data_dir_path, output_dir_path, gpus]
    proc = subprocess.Popen(cmd)
    proc.communicate()

    cmd2 = ['mv', output_dir_path, model_dir]
    proc = subprocess.run(cmd2)


def pred(struct_path, model_dir, **kwargs):
    struct = json.load(open(struct_path, 'r'))

    # Default GPU settings
    gpus = kwargs.get('gpus', '')

    # Create Dataset
    tmp_dir = tempfile.TemporaryDirectory()

    data_dir = os.path.join(tmp_dir.name, 'data_dir')
    os.makedirs(data_dir, exist_ok=True)

    blank_txts = format.struct_to_rd_bio_empty(struct)
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

    # Initialize RD Pred List if not existent
    if 'rd_preds' not in struct:
        struct['rd_preds'] = []
    if 'rd_evals' not in struct:
        struct['rd_evals'] = []
    if 'rd_metadata' not in struct:
        struct['rd_metadata'] = []

    rd_preds_dict = dict()

    # Make prediction per documents
    rd_labs = set()
    print('Making document predictions...')
    for doc_id in tqdm(blank_txts):
        doc_data_dir = os.path.join(data_dir, doc_id)
        doc_output_dir = doc_data_dir
        pred_cmd = os.path.join(dir_path, 'BERT', 'pred.sh')
        cmd = ['/bin/bash', pred_cmd, doc_data_dir, model_dir, doc_output_dir]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        proc.communicate()

        tags_path = os.path.join(doc_output_dir, 'test.tags.preds')
        doc_tags_path = os.path.join(doc_output_dir, 'test.preds')
        doc_struct = struct['documents'][doc_id]
    
        with open(doc_tags_path, 'r') as tags_file:
            lines = [l.strip() for l in tags_file.readlines()]

            pars_toks = []
            pars_tags = []

            # Get all labels in documents
            # doc_labs = set([l.replace('B-', '').replace('I-', '') for l in lines if l not in ['O', '']])

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
                        l = l.split(' ')
                        l = l + (['O'] * (2 - len(l)))
                        tok, tag = l
                        ptags.append(tag)
                        ptoks.append(tok)

                    pars_tags.append(ptags)
                    pars_toks.append(ptoks)

                i = j

            # num paragraphs >= num of paragraph preds
            # print('Num par tags: ', len(pars_tags))
            # print('Num pars:', len(
            #     struct['documents'][doc_id]['paragraphs']))


            # Get document labels
            doc_labs = list(reduce(lambda a,b: a + b, pars_tags))
            doc_labs = set([l[2:] for l in doc_labs if l[:2] in ['B-', 'I-']])
            rd_labs |= doc_labs

            # Save predictions, group by paragraph.
            #pars_toks, pars_tags

            doc_preds = []
            prev_toks = None
            current_entry = []
            j = 0
            while j < len(pars_tags):
                # print('Iteration {} of {}'.format(j, len(pars_tags)))
                current_toks = pars_toks[j]

                if current_toks != prev_toks:
                    if len(current_entry) == 0:
                        # at least one entry per par
                        assert(prev_toks is None)
                    else:
                        doc_preds.append(current_entry)
                        current_entry = []
                
                current_entry.append({
                    'toks': pars_toks[j], # needed for matching paragraph because some pars don't have desc and will be skipped
                    'tags': pars_tags[j],
                    'spans': format.make_spans(pars_tags[j], all_labels=doc_labs)
                })

                prev_toks = current_toks
                j += 1
            
            # Last paragraph has at least one entry
            assert(len(current_entry) > 0)
            doc_preds.append(current_entry)

            # Each entry is list of dictionary predictions (one per desc)
            rd_preds_dict[doc_id] = doc_preds

    struct['rd_preds'].append(rd_preds_dict)

    ## Evaluation ##

    # Get all RD annotations
    rd_annotations = []
    rd_predictions = []

    for doc_id in rd_preds_dict:
        orig_pars = struct['documents'][doc_id]['paragraphs']
        for orig_par in orig_pars:
            if ('annotated' not in orig_par) or (not orig_par['annotated']):
                continue

            orig_toks = orig_par['text'].split(' ')
            ner_annotations = orig_par['bio_annotations']

            for pred_par in rd_preds_dict[doc_id]:
                no_p_toks = [t for t in pred_par[0]['toks'] if t not in ['[P1]', '[P2]']]

                if no_p_toks == orig_toks: #match!
                    for entry in pred_par:
                        p1_idx = entry['toks'].index('[P1]')
                        p2_idx = entry['toks'].index('[P2]')

                        entry_pred_tags = [l if l[2:] in rd_labs else 'O' for l in entry['tags']]
                        entry_ann_tags = [l if l[2:] in rd_labs else 'O' for l in ner_annotations]
                        entry_ann_tags.insert(p1_idx, '0')
                        entry_ann_tags.insert(p2_idx, '0')

                        rd_predictions.extend(entry_pred_tags)
                        rd_annotations.extend(entry_ann_tags)
            
    labels = [[f'B-{l}', f'I-{l}'] for l in rd_labs]
    labels = list(reduce(lambda a,b: a + b, labels))
    labels.sort(key=lambda s:s[::-1])

    if len(rd_annotations) > 0:
        pred_eval = {
            'precision': precision_score(rd_annotations, rd_predictions, average='micro', labels=labels),
            'recall': recall_score(rd_annotations, rd_predictions, average='micro', labels=labels),
            'f1': f1_score(rd_annotations, rd_predictions, average='micro', labels=labels),
        }
    else:
        pred_eval = {
            'error': 'No annotations available.'
        }

    struct['rd_metadata'].append(metadata)
    struct['rd_evals'].append(pred_eval)

    return struct

if __name__ == '__main__':
    import json
    output_model_dir = '/data/rsg/nlp/juanmoo1/projects/02_takeda_dev/00_takeda/tmp/model'
    struct_path = '/data/rsg/nlp/juanmoo1/projects/02_takeda_dev/00_takeda/tmp/changed.json'
    with open(struct_path, 'r') as f:
        struct = json.load(f)
        train(struct, output_model_dir)
