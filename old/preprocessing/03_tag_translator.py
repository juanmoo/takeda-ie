'''
This script defines the procedures to translate between different tagging formats. Currently, there are three
different formats we consider:

(1) Structured Document [STRUCT]
(2) BIES Tagging Scheme [BMES]
(3) BIO Tagging Scheme [BIO]

Translation between all these formats is supported, however, due to the constraint in both (2) and (3) that entities
must be non-overlapping, translation of (1 -> 2) and (1 -> 3) is lossy.
'''

import codecs
import os
import json
import tqdm
import re
from argparse import ArgumentParser
from spacy.lang.en import English
from functools import reduce

# Defaults #
nlp = English()
tokenizer = nlp.Defaults.create_tokenizer(nlp)

default_label_map = {
    'authors': 'AUTH',
    'study_type': 'STYPE',
    'arm_description': 'DESC',
    'arm_dosage': 'DOSAGE',
    'arm_efficacy_metric': 'METRIC',
    'arm_efficacy_results': 'RESULTS'
}

# -- BMES -- #


def struct_to_bmes(ifile, label_map=default_label_map):
    struct = json.load(ifile)
    fnames = struct.keys()
    bmes_list = []
    for fname in fnames:
        paragraphs_bmes = []
        for entry in struct[fname]['paragraphs']:
            text = tokenizer(entry['text']).text
            bmes_tokens = text.split()
            bmes_annotations = ['O |'] * len(bmes_tokens)

            lmin = None
            lmax = None
            for k in [e for e in entry.keys() if e.endswith('-spans') and 'title' not in e]:
                key = k[:-6]
                key = label_map.get(key, key)

                for start, stop in entry[k]:
                    # For tokens that were annotated multiple times, ranges take precedence over singletons
                    for i in range(start, stop):
                        if bmes_annotations[i] != 'O |':
                            lmin = start if not lmin else min(lmin, start)
                            lmax = stop if not lmax else max(lmax, stop)
                        else:
                            bmes_annotations[i] = ''

                        if i == start:
                            if i == stop - 1:
                                bmes_annotations[start] += f' S-{key} |'
                            else:
                                bmes_annotations[i] += f' B-{key} |'
                        elif i == stop - 1:
                            bmes_annotations[i] += f' E-{key} |'
                        else:
                            bmes_annotations[i] += f' I-{key} |'

            bmes_annotations = list(map(lambda s: s[:-2], bmes_annotations))

            # Merge identical tags
            all_merged = True
            for j, a in enumerate(bmes_annotations):
                tags = list(set([e.strip() for e in a.split('|')]))
                if len(tags) == 1:
                    bmes_annotations[j] = tags[0]
                else:
                    all_merged = False

            bmes = list(zip(bmes_tokens, bmes_annotations))

            # Add delimiters in places where disagreeing overlapping annotations
            # occur in defined range.
            if lmin and lmax and not all_merged:
                bmes.insert(lmax, '^-' * 20 + 'STOP' + '-^' * 20)
                bmes.insert(lmin, 'v-' * 20 + 'START' + '-v' * 20)

            bmes = '\n'.join([' '.join(p) for p in bmes])
            paragraphs_bmes.append(bmes)
        bmes_list.append(paragraphs_bmes)
    return dict(zip(fnames, bmes_list))


# -- BIO -- #
def struct_to_bio(ifile, label_map=default_label_map):
    struct = json.load(ifile)
    fnames = struct.keys()
    bmes_list = []
    for fname in fnames:
        paragraphs_bmes = []
        for entry in struct[fname]['paragraphs']:
            text = tokenizer(entry['text']).text
            bmes_tokens = text.split()
            bmes_annotations = ['O |'] * len(bmes_tokens)

            lmin = None
            lmax = None
            for k in [e for e in entry.keys() if e.endswith('-spans') and 'title' not in e]:
                key = k[:-6]
                key = label_map.get(key, key)

                for start, stop in entry[k]:
                    # For tokens that were annotated multiple times, ranges take precedence over singletons
                    for i in range(start, stop):
                        if bmes_annotations[i] != 'O |':
                            lmin = start if not lmin else min(lmin, start)
                            lmax = stop if not lmax else max(lmax, stop)
                        else:
                            bmes_annotations[i] = ''

                        if i == start:
                            bmes_annotations[i] += f' B-{key} |'
                        else:
                            bmes_annotations[i] += f' I-{key} |'

            bmes_annotations = list(map(lambda s: s[:-2], bmes_annotations))

            # Merge identical tags
            all_merged = True
            for j, a in enumerate(bmes_annotations):
                tags = list(set([e.strip() for e in a.split('|')]))
                if len(tags) == 1:
                    bmes_annotations[j] = tags[0]
                else:
                    all_merged = False

            bmes = list(zip(bmes_tokens, bmes_annotations))

            # Add delimiters in places where disagreeing overlapping annotations
            # occur in defined range.
            if lmin and lmax and not all_merged:
                bmes.insert(lmax, '^-' * 20 + 'STOP' + '-^' * 20)
                bmes.insert(lmin, 'v-' * 20 + 'START' + '-v' * 20)

            bmes = '\n'.join([' '.join(p) for p in bmes])
            paragraphs_bmes.append(bmes)
        bmes_list.append(paragraphs_bmes)
    return dict(zip(fnames, bmes_list))


# BIO -> BMES #
def bio_to_bmes(ifile):
    conll = ifile.read()
    conll = conll.split('\n')
    pairs = [re.sub('\s+', ' ', e).split() for e in conll]
    pairs = [p + [''] * (2 - len(p)) for p in pairs]
    tokens, labels = zip(*pairs)

    new_labs = []
    for i, l in enumerate(labels):
        if l.startswith('B-'):
            if (i == len(labels) - 1) or labels[i + 1] != l.replace('B-', 'I-'):
                new_labs.append(l.replace('B-', 'S-'))
            else:
                new_labs.append(l)
        elif l.startswith('I-'):
            if (i == len(labels) - 1) or labels[i + 1] != l:
                new_labs.append(l.replace('I-', 'E-'))
            else:
                new_labs.append(l)
        else:
            new_labs.append(l)
    new_pairs = list(zip(*[tokens, new_labs]))
    bmes = '\n'.join(' '.join(p) for p in new_pairs)

    return bmes

# BMES -> BIO #


def bmes_to_bio(ifile):
    lines = [l.strip().split(' ') for l in ifile.readlines()]
    lines = [l + [''] * (2 - len(l)) for l in lines]

    tokens, labels = zip(*lines)
    prefixes, categories = zip(*[l.strip().split('-') if l.strip() not in ['O', ''] else [l.strip(), ''] for l in labels])
        
    prefix_map = {
        'B': 'B',
        'I': 'I',
        'E': 'I',
        'S': 'B'
    }
    bio_prefixes = [prefix_map.get(p, p) for p in prefixes]
    bio_labels = ['-'.join(pair) if pair[0].strip() not in ['', 'O']
                  else pair[0] for pair in zip(bio_prefixes, categories)]
    bio_lines = ['{} {}'.format(*pair) if pair[0].strip()
                 else '' for pair in zip(tokens, bio_labels)]
    bio = '\n'.join(bio_lines)
    return bio


if __name__ == '__main__':

    supported_formats = {'BMES': '.bmes', 'BIO': '.conll', 'STRUCT': '.json'}

    # Set translation handlers
    handlers = dict()
    handlers[('STRUCT', 'BMES')] = struct_to_bmes
    handlers[('STRUCT', 'BIO')] = struct_to_bio
    handlers[('BIO', 'BMES')] = bio_to_bmes
    handlers[('BMES', 'BIO')] = bmes_to_bio

    def not_implemented(**kwargs): raise NotImplementedError(
        'The requested translation direction is not yet supported.')
    pairs = [(a, b) for a in supported_formats for b in supported_formats if (
        a, b) not in handlers]
    for p in pairs:
        handlers[p] = not_implemented

    parser = ArgumentParser('<script>')

    parser.add_argument('input_path', type=str,
                        help='Path to directory that contains file(s) of interest.')
    parser.add_argument('output_path', type=str,
                        help='Path to directory where output(s) is(are) to be placed.')
    parser.add_argument('--source', type=str,
                        help=f'Choice from {sorted(list(supported_formats.keys()))}. [STRUCT is default]', default='STRUCT')
    parser.add_argument(
        '--target', type=str, help=f'Choice from {sorted(list(supported_formats.keys()))}. [BMES is default]', default='BMES')
    parser.add_argument('--label_map', type=str,
                        help='Path to JSON file containing desired label mappings.', default=dict())
    parser.add_argument('--separate-documents', action='store_true', default=False,
                        help='If this flag is passed, the output will be separated in a per-document basis.')

    args = parser.parse_args()

    direction = (args.source, args.target)
    handler = handlers[direction]

    # Load Inputs
    if os.path.isdir(args.input_path):
        base_path = os.path.realpath(os.path.normpath(args.input_path))
        fnames = [f for f in os.listdir(base_path) if f.lower().endswith(
            supported_formats[args.source.upper()])]
    else:
        path = os.path.normpath(args.input_path)
        path = os.path.realpath(path)
        base_path, fname = os.path.split(path)
        fnames = [fname]

    # Transform and Save
    for f in tqdm.tqdm(fnames):
        with codecs.open(os.path.join(base_path, f), 'rb', encoding='utf-8', errors='replace') as ifile:
            res = handler(ifile)

            if args.source.upper() == 'STRUCT':
                if args.separate_documents:
                    for key in res:
                        with codecs.open(os.path.join(args.output_path, key + supported_formats[args.target.upper()]), 'wb', encoding='utf-8', errors='replace') as ofile:
                            ofile.write('\n\n'.join(res[key]))
                else:
                    with codecs.open(os.path.join(args.output_path, 'output' + supported_formats[args.target.upper()]), 'wb', encoding='utf-8', errors='replace') as ofile:
                        for key in res:
                            ofile.write('\n'.join(res[key]))
                            ofile.write('\n')
            else:
                source_extension = supported_formats[args.source.upper()]
                target_extension = supported_formats[args.target.upper()]
                with codecs.open(os.path.join(args.output_path, f.replace(source_extension, target_extension)), 'wb', encoding='utf-8') as ofile:
                    ofile.write(res)
