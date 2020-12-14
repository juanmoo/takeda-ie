# split data into train/dev/test
# No oversampling (see line 43)
# Removed non-utf-8 characters (see lines 64-70)

import argparse
import os
import numpy as np
import pandas as pd
import random
import codecs
import re
import json


class DataProcessor(object):
    def __init__(self, oversample_rate=3):
        self.oversample_rate = oversample_rate

    def get_full_dataset(self, input_path):
        # Normalize Path
        input_path = os.path.normpath(input_path)
        input_path = os.path.realpath(input_path)

        # Read Files
        fnames = [f for f in os.listdir(input_path) if f.lower().split(
            '.')[-1] in ['bmes', 'conll']]
        files = [codecs.open(os.path.join(input_path, fname), 'rb',
                             encoding='utf-8', errors='ignore').read().strip() for fname in fnames]

        # Read files into paragraphs
        paragraphs = []
        for text in files:
            lines = text.split('\n')
            lines = [re.sub('\s+', '\t', l.strip()) for l in lines]
            data = []
            sentence = []
            for line in lines:
                line = line.strip()
                if len(line) == 0:
                    if len(sentence) > 0:
                        data.append(sentence)
                        sentence = []
                    continue
                token, tag = line.split('\t')
                sentence.append((token, tag))

            if len(sentence) > 0:
                data.append(sentence)
            paragraphs.append(data)

        # Create DataFrame from paragraphs
        all_data = []
        paragraph_count = 0
        for fname, pars in zip(fnames, paragraphs):
            doc_data = []
            fname = fname[:fname.rfind('.')]

            for j_par, par in enumerate(pars):
                toks, labs = zip(*par)
                doc_data.append({
                    'doc_id': fname,
                    'paragraph_id': paragraph_count,
                    'par_loc': j_par,
                    'tokens': toks,
                    'labels': labs,
                    'par_count': len(toks)
                })
                paragraph_count += 1
            all_data.extend(doc_data)
        data = pd.DataFrame(all_data)

        return data

    def random_split_document(self, data, test_frac=0.2):
        counts = []
        total_count = 0
        for doc_id, series in data.groupby('doc_id').count()[['paragraph_id']].iterrows():
            count = series[0]
            total_count += count
            counts.append((doc_id, count))

        random.shuffle(counts)
        train_target_count = total_count * (1 - test_frac)

        train_docs = []
        train_par_count = 0
        j = 0
        while train_par_count < train_target_count:
            doc_id, count = counts[j]
            train_docs.append(doc_id)
            train_par_count += count
            j += 1

        test_docs = []
        test_par_count = 0
        while j < len(counts):
            doc_id, count = counts[j]
            test_docs.append(doc_id)
            test_par_count += count
            j += 1

        train_frac = train_par_count/total_count
        test_frac = test_par_count/total_count

        data_train = data.loc[data['doc_id'].isin(train_docs)]
        data_test = data.loc[data['doc_id'].isin(test_docs)]

        split_info = {
            'split_style': 'Document Split',
            'train_docs': train_docs,
            'test_docs': test_docs,
            'test_frac': test_frac,
        }

        return data_train, data_test, split_info

    def random_split_paragraph(self, data, test_frac=0.2):
        paragraph_ids = list(pd.unique(data['paragraph_id']))
        random.shuffle(paragraph_ids)

        test_count = int(len(paragraph_ids) * (1 - test_frac))
        train_idxs = set(paragraph_ids[:test_count])
        test_idxs = set(paragraph_ids[test_count:])

        data_train = data.loc[data['paragraph_id'].isin(train_idxs)]
        data_test = data.loc[data['paragraph_id'].isin(test_idxs)]

        total_count = data.sum()['par_count']
        test_count = data_test.sum()['par_count']
        test_frac = test_count/total_count

        split_info = {
            'split_style': 'Paragraph Split',
            'test_frac': test_frac,
        }

        return data_train, data_test, split_info

    def oversample(self, data, oversample_rate=1):
        df_len = len(data)
        df = data.copy()

        for j, row in data.iterrows():
            if j > df_len:
                break

            if len(set(row['labels'])) > 0:
                for _ in range(int(oversample_rate - 0.5)):
                    df = df.append(row, ignore_index=True)
        return df

    def create_bio(self, data):
        par_tokens = data['tokens'].to_numpy()
        par_labels = data['labels'].to_numpy()

        output = ''
        for toks, labs in zip(par_tokens, par_labels):
            for t, l in zip(toks, labs):
                output += '{:<20}{}\n'.format(t, l)
            output += '\n'
        return output

    def split_train_test(self, input_path, output_dir, ratio=0.2, document_level_split=False):
        data = self.get_full_dataset(input_path)

        if document_level_split:
            train, test, info = self.random_split_document(data, ratio)
        else:
            train, test, info = self.random_split_paragraph(data, ratio)

        # Oversample
        train = self.oversample(train, oversample_rate=self.oversample_rate)

        os.makedirs(output_dir, exist_ok=True)
        # Save Training Data
        with open(os.path.join(output_dir, "train.txt"), "w", encoding='utf-8') as f:
            f.write(self.create_bio(train))

        # Save Test/Dev Data
        with open(os.path.join(output_dir, "valid.txt"), "w", encoding='utf-8') as f:
            f.write(self.create_bio(test))

        # Save Split Metadata
        with open(os.path.join(output_dir, 'split_info.json'), 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=4)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--oversample-rate", type=int, default=1,
                        help="Oversampling rate for paragraphs with annotations.")
    parser.add_argument("input_files", type=str,
                        help="Path to the full dataset.")
    parser.add_argument("output_dir", type=str,
                        help="Directory for saving the output files.")
    parser.add_argument('--document-split',
                        action="store_true", default=False)

    args = parser.parse_args()
    processor = DataProcessor(oversample_rate=args.oversample_rate)

    processor.split_train_test(
        input_path=args.input_files, output_dir=args.output_dir, document_level_split=args.document_split)
