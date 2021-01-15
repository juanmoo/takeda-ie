'''
Logic for sampling structs
'''

import os
import json
import random
import numpy as np

def split_struct(struct_path, output_dir, test_frac=0.2, paragraph_split=False, **kwargs):
    # Read Struct
    struct = None
    with open(struct_path, 'r') as struct_file:
        struct = json.load(struct_file)

    doc_ids = list(struct['documents'].keys())
    doc_ids.sort()

    # Get Paragraph Counts
    par_counts = {}
    offsets = {}
    running_count = 0
    for doc_id in doc_ids:
        doc_count = len(struct['documents'][doc_id]['paragraphs'])
        par_counts[doc_id] = doc_count
        offsets[doc_id] = running_count

        running_count += doc_count


    total_count = running_count
    # Determin whether or not a paragraph is included in training set
    assignment = np.array([False] * total_count, dtype=bool)

    train_frac = 1.0 - test_frac
    num_train_target = int(train_frac * total_count + 0.5)
    num_train_pars = 0

    if paragraph_split:
        print('Train par count: {}'.format(num_train_target))
        num_train_pars = num_train_target
        assignment[:num_train_target] = [True] * num_train_target
        np.random.shuffle(assignment)

    else:
        rng = np.random.default_rng()
        ids = np.array(doc_ids)
        rng.shuffle(ids)

        for doc_id in ids:
            if num_train_pars <= num_train_target:
                # assign paragraphs to train set
                num_train_pars += par_counts[doc_id]
                o = offsets[doc_id]
                assignment[o: o + par_counts[doc_id]] = True
            else:
                break

    # Copy all non-document elements to train and test structs
    train_struct = dict()
    test_struct = dict()

    for k in struct.keys():
        if k == 'documents':
            continue
        train_struct[k] = struct[k]
        test_struct[k] = struct[k]

    train_struct['documents'] = {}
    test_struct['documents'] = {}

    # Copy assigned document paragraphs
    for doc_id in struct['documents']:
        train_pars = []
        test_pars = []

        offset = offsets[doc_id]
        par_count = par_counts[doc_id]
        doc_assignment = assignment[offset: offset + par_count]
        doc_struct = struct['documents'][doc_id]
        print('pars from document: {}'.format(sum(doc_assignment)))

        for j, par in enumerate(doc_struct['paragraphs']):
            if doc_assignment[j]:
                train_pars.append(par)
            else:
                test_pars.append(par)

        if len(train_pars) > 0:
            doc_struct_train = {k:doc_struct[k] for k in doc_struct if k != 'paragraphs'}
            doc_struct_train['paragraphs'] = train_pars
            train_struct['documents'][doc_id] = train_pars


        if len(test_pars) > 0:
            doc_struct_test = {k:doc_struct[k] for k in doc_struct if k != 'paragraphs'}
            doc_struct_test['paragraphs'] = test_pars
            test_struct['documents'][doc_id] = test_pars

    # Save Structs
    basename = os.path.basename(struct_path).replace('.json', '')
    train_name = basename + '_train.json'
    train_path = os.path.join(output_dir, train_name)
    with open(train_path, 'w') as train_file:
        json.dump(train_struct, train_file, indent=4)

    test_name = basename + '_test.json'
    test_path = os.path.join(output_dir, test_name)
    with open(test_path, 'w') as test_file:
        json.dump(test_struct, test_file, indent=4)

    return train_struct, test_struct


if __name__ == '__main__':
    struct_path = '/data/rsg/nlp/juanmoo1/projects/02_takeda_dev/00_takeda/tmp/structs/struct2.json'
    output_path = '/data/rsg/nlp/juanmoo1/projects/02_takeda_dev/00_takeda/tmp/structs/splits'

    split_struct(struct_path, output_path, test_frac=0.8, paragraph_split=False)

