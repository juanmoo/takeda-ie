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
