'''
This script validates the integrity of the syntax of BIO corpora
'''

import os
import argparse
import tqdm
import re

ext_list = ['bio', 'conll', 'bmes']


def verify_file(path):
    print(f'Verifying file at {path}')

    with open(path, 'r') as ifile:
        lines = ifile.readlines()
    
    par_count = 0
    curr_lab = 'O'
    curr_start = -1
    for j, l in enumerate(lines):
        l = re.sub('\s+', ' ', l).strip()

        if len(l) == 0: # new paragraph
            curr_lab = '0'
            curr_start = j
            par_count += 1
        
        else:
            elts = l.split(' ')
            if len(elts) != 2:
                raise Exception(f'Unable to find matching token/label in paragraph {par_count}, line {j + 1}.')
            _, lab = elts

            if lab == 'O':
                curr_lab = 'O'
                curr_start = j

            else:
                prefix, lab = lab.split('-')
                if prefix == 'B':
                    curr_start = j
                    curr_lab = lab
                elif prefix == 'I':
                    if lab != curr_lab:
                        raise Exception(f'Unable to find start for I label in paragraph {par_count} in line {j + 1}.')
    
    print(f'Found no syntax errors in {j + 1} lines and {par_count + 2} paragraphs')


def main(dir):
    dir_path = os.path.normpath(dir)
    dir_path = os.path.realpath(dir_path)
    fnames = [p for p in os.listdir(
        dir_path) if p[p.rfind('.') + 1:].lower() in ext_list]

    for fname in fnames:
        fpath = os.path.join(dir_path, fname)
        verify_file(fpath)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dir', type=str, help='Input directory')
    parser.add_argument('--type', type=str, help='BIO or BMES', default='BIO')

    args = parser.parse_args()

    main(args.input_dir)
