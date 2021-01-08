'''
STRUCT to RD Task Input
'''

import json
import argparse
import os
from spacy.lang.en import English
from tqdm import tqdm

# Global Initialization
default_trigger = 'arm_description'
default_foi = ['arm_efficacy_metric', 'arm_efficacy_results', 'arm_dosage']
nlp = English()
nlp.add_pipe(nlp.create_pipe('sentencizer'))


def get_sentences(text):
    doc = nlp(text)
    return [sent.string.strip() for sent in doc.sents]


def get_segment(interval, boundaries, window=3):
    cxt = int((window - 1) / 2)
    start, end = interval
    sent_idx_start = 0
    sent_idx_end = 0

    for i, b in enumerate(boundaries):
        if start >= b:
            sent_idx_start = i
            sent_idx_end = i
        
        if end - 1 < boundaries[i+1]:
            sent_idx_end = i
            break

    segment_start = boundaries[max(0, sent_idx_start - cxt)]
    segment_end = boundaries[min(len(boundaries) - 1, sent_idx_end + cxt + 1)]
    
    return (segment_start, segment_end)


def process_document(doc_struct, foi=default_foi, trigger=default_trigger):
    data = []
    trigger_span_key = f'{trigger}-spans'
    trigger_arm_key = f'{trigger}-arms'

    for par in doc_struct['paragraphs']:

        # Skip paragraphs w/o trigger entities
        if trigger_span_key not in par or len(par[trigger_span_key]) == 0:
            continue

        text = par['text']
        tokens = text.strip().split(' ')
        sentences = get_sentences(text)

        sent_boundaries = [0]
        for sent in sentences:
            sent_boundaries.append(
                len(sent.strip().split(' ')) + sent_boundaries[-1])

        for span, trigger_arm in zip(par[trigger_span_key], par[trigger_arm_key]):
            seg_start, seg_end = get_segment(span, sent_boundaries, window=1)

            tagged_text = []
            for token in tokens:
                tagged_text.append([token, 'O'])

            # assign B/I- tags to each token
            # print('Keys: ', par.keys())
            for field in foi:
                field_span_key = f'{field}-spans'
                field_arm_key = f'{field}-arms'

                if not field_span_key in par:
                    # print(f'{field_span_key} not found. Skipping!')
                    continue

                fval_spans = par[field_span_key]
                fval_arms = par[field_arm_key]
                # print(fval_spans)

                for fval_span, fval_arm in zip(fval_spans, fval_arms):
                    # Add annotation for all non-arm entities and arm entities 
                    # that match the arm of the trigger word
                    if fval_arm == -1 or fval_arm == trigger_arm:
                        start, end = fval_span
                        tagged_text[start][1] = f'B-{field}'
                        if end == start + 1:
                            continue
                        for i in range(start+1, end):
                            tagged_text[i][1] = f'I-{field}'

            prod_span_start, prod_span_end = span
            tagged_text.insert(prod_span_start, ["[P1]", "O"])
            tagged_text.insert(prod_span_end + 1, ["[P2]", "O"])

            tagged_segment = tagged_text[seg_start:(seg_end+2)]
            data.append(tagged_segment)

    bio_pars = ['\n'.join(['{}\t{}'.format(t, l) for (t, l) in par_toks]) for par_toks in data]
    output = '\n\n'.join(bio_pars)

    return output


if __name__ == '__main__':
    argparse = argparse.ArgumentParser()
    argparse.add_argument('input_file', type=str, help='Path to input struct')
    argparse.add_argument('output_dir', type=str,
                          help='Path to output directory')

    args = argparse.parse_args()

    input_file = args.input_file
    input_file = os.path.normpath(input_file)
    input_file = os.path.realpath(input_file)

    struct = None
    with open(input_file, 'r') as ifile:
        struct = json.load(ifile)

    assert(struct is not None)

    # Create output directory if it doesn't exist
    output_dir = args.output_dir
    output_dir = os.path.normpath(output_dir)
    output_dir = os.path.realpath(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    print('Processing Documents ... ')
    for doc_id in tqdm(struct):
        doc_struct = struct[doc_id]
        bio_out = process_document(doc_struct)
        fout_path = os.path.join(output_dir, doc_id) + '.bio'

        with open(fout_path, 'w') as ofile:
            ofile.write(bio_out)

    print('Done!')
