'''
Script to transform directory of bio documents into STRUCT format.

STRUCT: 

{
    doc_id: {
        'doc_name': name, // missing
        paragraphs: [
            {
                text: "... <str> ...",
                forall keys K:
                k-spans: [(start_i, stop_i) forall i],
                k-arms: [arm_i forall i] //missing
            },
            ...
        ]
    },
    ...
}
'''

import argparse
import os
import re
import json

def load_bio_doc(path):
    path = os.path.realpath(path)
    path = os.path.normpath(path)

    paragraphs = []
    current_par = []
    with open(path, 'r') as ifile:
        lines = ifile.readlines()
        for l in lines:
            l = re.sub('\s+', ' ', l).strip()
            if len(l) == 0:
                if len(current_par) > 0:
                    paragraphs.append(current_par)
                current_par = []
            else:
                current_par.append(l)

        if len(current_par) > 0:
            paragraphs.append(current_par)
    
    par_structs = []
    for par in paragraphs:
        tokens, labels = zip(*[l.split(' ') for l in par])
        par_text = ' '.join(tokens)
        par_dict = {'text': par_text}

        prev_lab = 'O'
        prev_start = -1
        for j, l in enumerate(labels):
            if not l.endswith(prev_lab):
                if prev_lab != 'O':
                    span_key = f'{prev_lab}-spans'
                    if span_key not in par_dict:
                        par_dict[span_key] = []
                    par_dict[span_key].append((prev_start, j))
                prev_lab = 'O' if l == 'O' else l.split('-')[1]
                prev_start = j
        
        if prev_lab != 'O':
            span_key = f'{prev_lab}-spans'
            if span_key not in par_dict:
                par_dict[span_key] = []
            par_dict[span_key].append((prev_start, len(tokens)))
        par_structs.append(par_dict)

    return par_structs









if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dir', type=str, help='Path to directory with input files.')
    parser.add_argument('output_path', type=str, help='Path to output file.')
    args = parser.parse_args()

    input_dir = os.path.realpath(args.input_dir)
    input_dir = os.path.normpath(input_dir)

    struct = {}
    fnames = os.listdir(input_dir)
    for fname in fnames:
        path = os.path.join(input_dir, fname)
        pars_struct = load_bio_doc(path)
        doc_id = os.path.basename(path)
        doc_id = doc_id[:doc_id.rfind('.')]
        struct[doc_id] = {
            'paragraphs': pars_struct
        }
    
    # Save struct as JSON
    output_path = args.output_path
    output_path = os.path.realpath(output_path)
    output_path = os.path.normpath(output_path)

    dirname = os.path.dirname(output_path)
    os.makedirs(dirname, exist_ok=True)
    with open(output_path, 'w') as ofile:
        json.dump(struct, ofile, indent=4)