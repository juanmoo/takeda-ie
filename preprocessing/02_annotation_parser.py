import argparse
import pandas as pd
import json
import codecs
# from spacy.lang.en import English

# -- Defaults -- #
relevant_entities = ['title', 'authors', 'study_type', 'arm_efficacy_metric',
                     'arm_efficacy_results', 'arm_description', 'arm_dosage']

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
                    j = 0
                    while f'{k}-{j}' in entry or j < 1:
                        # Add number if j > 0
                        knum = f'{k}-{j}' if j > 0 else k
                        if knum in entry and entry[knum] and entry[knum + '-tag']:
                            print(f'Extracting {knum}')
                            k_locs = get_locs(entry[knum + '-tag'])
                            if f'{k}-spans' not in paragraph_entry:
                                paragraph_entry[f'{k}-spans'] = []
                                paragraph_entry[f'{k}-arms'] = []
                            paragraph_entry[f'{k}-spans'].extend(
                                get_spans(k_locs))
                            paragraph_entry[f'{k}-arms'].extend(
                                [int(entry['arm_number'])] * (len(k_locs)//2))
                            assert(
                                len(paragraph_entry[f'{k}-spans']) == len(paragraph_entry[f'{k}-arms']))
                        j += 1

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
            bmes_annotations = ['O |'] * len(bmes_tokens)

            lmin = None
            lmax = None
            for k in [e for e in entry.keys() if e.endswith('-spans') and 'title' not in e]:
                key = k[:-6]
                key = key_map.get(key, key)

                for start, stop in entry[k]:
                    # For tokens that were annotated multiple times, ranges take precedence over singletons
                    # bmes_annotations[start] == 'O':
                    for i in range(start, stop):
                        if bmes_annotations[i] not in ['O |']:
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

            # Merge tags that agree
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Parse annotations to JSON document.')
    parser.add_argument('annotations_path', type=str,
                        help='Path to annotations csv file.')
    parser.add_argument('output_path', type=str,
                        help='Path to output JSON file.')
    parser.add_argument('--config', type=str, required=False, default=None,
                        help='Path to JSON configuration file containing a list of relevant entities.')

    def parse_annotations(args):
        # Load Config
        if args.config:
            with codecs.open(args.config, 'rb', encoding='utf-8') as config_file:
                config = json.load(config_file)
        else:
            config = {}
        parsed = parse_csv(args.annotations_path, **config)

        # Save output
        with codecs.open(args.output_path, 'wb', encoding='utf-8', errors='replace') as outfile:
            json.dump(parsed, outfile, indent=4)

    args = parser.parse_args()
    parse_annotations(args)
