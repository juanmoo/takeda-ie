'''
Logic to create annotation tasks and digest annotation files
'''

import os
import json
import codecs
import pandas as pd
import csv

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
