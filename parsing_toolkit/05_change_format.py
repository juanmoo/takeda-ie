'''
Utility Script to change the chunking format of a set of annotations.
'''

import os
import sys
import codecs
import re
import argparse
from tqdm import tqdm

def conll_to_bmes(conll):
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
    bmes = '\n'.join('\t '.join(p) for p in new_pairs)

    return bmes

def main(input_dir, output_dir, direction):
    '''
    Transform all input files in input_dir and place in output_dir.
    '''
    if direction.upper() == 'CONLLTOBMES':
        input_ext = '.conll'
        output_ext = '.bmes'
        translator_function = conll_to_bmes
    else:
        print('Translation direction not yet supported.')
        return



    # Load Translate and Save
    files = [f for f in os.listdir(input_dir) if f.lower().endswith(input_ext)]

    for fname in tqdm(files):
        with codecs.open(os.path.join(input_dir, fname), 'r', encoding='utf-8', errors='ignore') as ifile:
            inp_text = ifile.read()
            out_text = translator_function(inp_text)
            with codecs.open(os.path.join(output_dir, fname.lower().replace(input_ext, output_ext)), 'wb', encoding='utf-8', errors='ignore') as ofile:
                ofile.write(out_text)



if __name__ == '__main__':
    parser = argparse.ArgumentParser('<script>')
    parser.add_argument('input_dir', type=str, help='Path to files to be transformed.')
    parser.add_argument('output_dir', type=str, help='Path to directory where transformed files are to be placed.')
    parser.add_argument('direction', type=str, help='Direction of translation (BMESTOCONLL or CONLLTOBMES)')

    args = parser.parse_args()
    main(args.input_dir, args.output_dir, args.direction)

