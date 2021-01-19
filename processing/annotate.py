'''
Logic to create annotation tasks and digest annotation files
'''

import os
import json
import codecs
import pandas as pd
import csv
from multiprocessing import Process
from tqdm import tqdm

# Create annotation tasks


def filter(data, par_min_len=25, par_max_len=300, keep_abstract=False, keep_discussion=False, **kwargs):

    # Constraints
    constraints = [
        lambda s: par_min_len <= len(
            s.split(' ')) <= par_max_len  # Length Constraint
    ]

    # Exceptions
    exceptions = [
        lambda s: s.lower().startswith('abstract') or kwargs.get(
            'keep_abstract', False)  # Abstract exception
    ]

    # Non description based constraints
    no_abstract_locs = (data['head'].apply(
        lambda s: (s.strip().lower()) != 'abstract' or keep_abstract))
    no_discussion_locs = (data['head'].apply(
        lambda s: ('discussion' not in s.strip().lower() or keep_discussion)))

    def should_include(s): return all(f(s)
                                      for f in constraints) or any(f(s) for f in exceptions)
    include_locs = data['text'].apply(
        should_include) & no_abstract_locs & no_discussion_locs

    return data[include_locs]


def create_annotation_tasks(struct_path, output_path, **kwargs):
    # normalize paths
    struct_path = os.path.normpath(struct_path)
    struct_path = os.path.realpath(struct_path)
    output_path = os.path.normpath(output_path)
    output_path = os.path.realpath(output_path)

    # Load data and create annotations
    with codecs.open(struct_path, 'rb', encoding='utf-8', errors='replace') as struct_file:
        struct = json.load(struct_file)

    data = []
    for doc_id in struct:
        doc_struct = struct[doc_id]

        doc_paragraphs = doc_struct['paragraphs']
        doc_id = doc_struct['document_id']
        file_name = doc_struct['file_name']
        title = doc_struct['title']

        for p in doc_paragraphs:
            position = p['position']
            text = p['text']
            head = p['head']
            data.append({
                'document_id': doc_id,
                'file_name': file_name,
                'title': title,
                'arm_number': 1,
                'position': position,
                'head': head,
                'text': text
            })
    data = pd.DataFrame(data).fillna('')

    # Apply Filters
    data = filter(data, **kwargs)

    # Create Annotation Task File
    data.to_csv(output_path, quoting=csv.QUOTE_ALL)

def load_annotations(input_struct, annotations_path, output_struct, **kwargs):

    ## Load Struct
    struct = None
    with open(input_struct, 'r') as struct_file:
        struct = json.load(struct_file)

    # Load Annotations
    annotations = pd.read_csv(annotations_path).fillna('')

    count = 0
    for doc_id in tqdm(struct['documents']):
        doc_struct = struct['documents'][doc_id]
        doc_struct = load_document_annotations(doc_struct, annotations)
        # p = Process(target=load_document_annotations, args=(doc_struct, annotations,))
        if doc_struct:
            struct['documents'][doc_id] = doc_struct
            count += 1
        else:
            print('Nothing to do for: {}'.format(doc_id))

    # Save annotated struct
    with open(output_struct, 'w') as output_file:
        json.dump(struct, output_file, indent=4)
    
    print('Annotated {} documents.'.format(count))

def get_spans(spans_str):
    idxs = [int(e) for e in spans_str.split(',') if len(e) > 0]
    assert(len(idxs)%2 == 0)
    return list(zip(idxs[::2], idxs[1::2]))


def load_document_annotations(doc_struct, annotations, **kwargs):

    doc_df = annotations.loc[annotations['doc_id'] == doc_struct['document_id']]

    if len(doc_df) == 0:
        return False

    non_arm_cols = ['title', 'authors', 'study_type']
    arm_non_numbered = ['arm_efficacy_metric', 'arm_efficacy_results']
    arm_numbered  = ['arm_dosage', 'arm_description']

    # Iterate over doc_struct paragraphs
    for par in doc_struct['paragraphs']:
        ann_par = annotations.loc[annotations['description'] == par['text']]
        bio_annotations = ['O'] * len(par['text'].strip().split(' '))

        for j, row in ann_par.iterrows():
            par['annotated'] = True

            # Get arm number
            arm_count = int(row['arm_number'])

            # Get annotations for non-arm columns
            for k in non_arm_cols:
                for kp in row.index:
                    if k in kp:
                        span_key = f'ann-{k}-spans'
                        arm_key = f'ann-{k}-arms'

                        spans = []
                        tags_col = f'{k}-tag'
                        span_str = row[tags_col]
                        spans = get_spans(span_str)
                        if span_key not in par:
                            par[span_key] = []
                            par[arm_key] = []
                        par[span_key].extend(spans)
                        par[arm_key].extend([-1] * len(spans))

                        if k != 'title':
                            for i, j in spans:
                                bio_annotations[i] = f'B-{k}'
                                for n in range(i + 1, j):
                                    bio_annotations[n] = f'I-{k}'
                        break

            # Get annotations for arm non-numbered columns
            for k in arm_non_numbered:
                for kp in row.index:
                    if k in kp:
                        span_key = f'ann-{k}-spans'
                        arm_key = f'ann-{k}-arms'

                        spans = []
                        tags_col = f'{k}-tag'
                        span_str = row[tags_col]
                        spans = get_spans(span_str)
                        if span_key not in par:
                            par[span_key] = []
                            par[arm_key] = []
                        par[span_key].extend(spans)
                        par[arm_key].extend([arm_count] * len(spans))

                        for i, j in spans:
                            bio_annotations[i] = f'B-{k}'
                            for n in range(i + 1, j):
                                bio_annotations[n] = f'I-{k}'
                        break
            
            # Get annotations for arm columns
            for k in arm_numbered:
                for kp in row.index:
                    if k in kp:

                        span_key = f'ann-{k}-spans'
                        arm_key = f'ann-{k}-arms'
                        spans = []
                        arms = []

                        dash_nums = [int(c[len(k) + 1:-4]) for c in row.index if c.startswith(k) and c.endswith('-tag')]

                        for dn in dash_nums:
                            tag_key = f'{k}-{dn}-tag'
                            span_str = row[tag_key]
                            spans_dn = get_spans(span_str)
                            arm_id = (arm_count, dn)
                            spans.extend(spans_dn)
                            arms.extend([arm_id] * len(spans_dn))
                        
                        if span_key not in par:
                            par[span_key] = []
                            par[arm_key] = []
                        par[span_key].extend(spans)
                        par[arm_key].extend(arms)

                        for i, j in spans:
                            bio_annotations[i] = f'B-{k}'
                            for n in range(i + 1, j):
                                bio_annotations[n] = f'I-{k}'

                        break
        if par['annotated']:
            par['bio_annotations'] = bio_annotations

    return doc_struct


if __name__ == '__main__':
    input_struct = '/data/rsg/nlp/juanmoo1/projects/02_takeda_dev/00_takeda/tmp/structs/annotations_test/test_docs.json'
    annotations_path = '/data/rsg/nlp/juanmoo1/projects/02_takeda_dev/00_takeda/tmp/structs/annotations_test/merged.csv'
    output_struct = '/data/rsg/nlp/juanmoo1/projects/02_takeda_dev/00_takeda/tmp/structs/annotations_test/test_docs2.json'

    load_annotations(input_struct, annotations_path, output_struct)