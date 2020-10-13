import os
import argparse
import pandas as pd
from spacy.lang.en import English

# -- Defaults -- #
relevant_entities = ['title', 'authors', 'study_type', 'arm_description',
                     'arm_dosage', 'arm_efficacy_metric', 'arm_efficacy_results']

bmes_label_map = {
    'authors': 'AUTH',
    'study_type': 'STYPE',
    'arm_description': 'DESC',
    'arm_dosage': 'DOSAGE',
    'arm_efficacy_metric': 'METRIC',
    'arm_efficacy_results': 'RESULTS'
}


# -- Initialization -- #
nlp = English()
tokenizer = nlp.Defaults.create_tokenizer(nlp)


# -- (CSV -> Structured Dict) -- #
def parse_csv(csv_path, relevant_entities=relevant_entities):
    parsed = dict()
    data = pd.read_csv(csv_path).fillna('')
    for doc_id in pd.unique(data['doc_id']):
        doc_data = data.loc[data['doc_id'] ==
                            doc_id].copy().reset_index(drop=True)
        parsed[doc_id] = {
            'doc_name': doc_data['doc_name'].iloc[0],
            'paragraphs': [],
        }

        print('Document: {}'.format(doc_id))
        paragraphs = []

        i = 0
        while i < len(doc_data):
            count = 0
            desc = doc_data.iloc[i]['description']
            paragraph_entry = dict()
            paragraph_entry['text'] = desc

            while i < len(doc_data) and doc_data.iloc[i]['description'] == desc:
                entry = doc_data.iloc[i]

                def get_locs(s): return [int(e.strip())
                                         for e in s.split(',') if e.strip()]
                def get_spans(l): return [(l[2 * i], l[2 * i + 1])
                                          for i in range(len(l)//2)]

                for k in relevant_entities:
                    if entry[k] and entry[k + '-tag']:
                        k_locs = get_locs(entry[k + '-tag'])
                        if f'{k}-spans' not in paragraph_entry:
                            paragraph_entry[f'{k}-spans'] = []
                        paragraph_entry[f'{k}-spans'].extend(get_spans(k_locs))

                # Counter Logic
                count += 1
                i += 1

            paragraphs.append(paragraph_entry)

        parsed[doc_id]['paragraphs'] = paragraphs
    return parsed


# -- (Structured Dict -> BMES) -- #
def make_bmes(data, key_map=bmes_label_map):
    fnames = data.keys()
    bmes_list = []
    for fname in fnames:
        paragraphs_bmes = []
        for entry in data[fname]['paragraphs']:
            text = tokenizer(entry['text']).text
            bmes_tokens = text.split()
            bmes_annotations = ['O'] * len(bmes_tokens)

            for k in [e for e in entry.keys() if e.endswith('-spans') and 'title' not in e]:
                key = k[:-6]
                key = key_map.get(key, key)

                for start, stop in entry[k]:
                    # For tokens that were annotated multiple times, ranges take presendence over singletons
                    if stop - start == 1 and bmes_annotations[start] == 'O':
                        bmes_annotations[start] = f'S-{key}'
                    else:
                        for i in range(start, stop):
                            if i == start:
                                bmes_annotations[i] = f'B-{key}'
                            elif i == stop - 1:
                                bmes_annotations[i] = f'M-{key}'
                            else:
                                bmes_annotations[i] = f'E-{key}'

            bmes = list(zip(bmes_tokens, bmes_annotations))
            bmes = '\n'.join([' '.join(p) for p in bmes])
            paragraphs_bmes.append(bmes)
        bmes_list.append(paragraphs_bmes)
    return dict(zip(fnames, bmes_list))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Turn annotations obtained with annotation tool into BMES')
    parser.add_argument('annotations_path', type=str,
                        help='Path to annotations csv file.')
    parser.add_argument('output_dir', type=str,
                        help='Directory where segmented BMES files are to be placed.')
    parser.add_argument('--config', type=str, required=False, default=None,
                        help='Path to JSON configuration file containing a list of relevant entities, bmes label mapping, or both.')
    parser.add_argument('--separate-documents', action='store_true', default=False,
                        help='Output will be separated into several BMES file if this flagged is passed')

    def create_bmes_cli(args):
        csv_kwargs = {}
        bmes_kwargs = {}
        if args.config:
            with open(args.config, 'r') as f:
                config = json.load(f)
                if 'relevant_entities' in config:
                    csv_kwargs['relevant_entities'] = config['relevant_entities']
                if 'label_map' in config:
                    bmes_kwargs['label_map'] = config['label_map']

        parsed = parse_csv(args.annotations_path, **csv_kwargs)
        data = make_bmes(parsed, **bmes_kwargs)

        if not args.separate_documents:
            with open(os.path.join(args.output_dir, 'output.bmes'), 'w') as f:
                for fname in data:
                    f.write('\n'.join(data[fname]))
                    f.write('\n')
        else:
            for fname in data:
                with open(os.path.join(args.output_dir, fname + '.bmes'), 'w') as f:
                    f.write('\n'.join(data[fname]))

    args = parser.parse_args()
    create_bmes_cli(args)
