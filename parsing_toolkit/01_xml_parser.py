import os
import csv
import uuid
import re
import pandas as pd
from bs4 import BeautifulSoup
from spacy.lang.en import English
import argparse

nlp = English()
tokenizer = nlp.Defaults.create_tokenizer(nlp)

# ----- Utils ----- #


def tokenize(text):
    text = ' '.join([t.text for t in tokenizer(text)])
    text = re.sub('\n+', '\n', text)
    text = re.sub('[ ]{2,}', ' ', text)
    text = '\n'.join([s.strip() for s in text.split('\n') if s.strip()])
    return text


def entry_creator(defaults):
    def f(description, **kwargs):
        entry = {**defaults}
        entry['description'] = description
        entry.update(kwargs)
        return entry
    return f

# ----- XML Parser -------- #


def parse_xml(file_path):
    with open(file_path, 'r') as f:
        soup = BeautifulSoup(f.read(), features="html.parser")
        data = []

        # No producer ID for now, just use a random UUID
        doc_id = str(uuid.uuid4())
        fname = os.path.basename(file_path).replace('.xml', '')
        make_entry = entry_creator({
            'doc_id': doc_id,
            'doc_name': fname.strip().replace('.xml', ''),
            'arm_number': '1',
            'position': 'Document Description',
        })

        ## File Description Data ##
        doc_desc = soup.find('filedesc')
        raw_desc = ''
        for c in doc_desc.find_all():
            if c.text:
                raw_desc += ' ' + c.text.strip()
        raw_desc = tokenize(raw_desc)

        # Join all < 3 word paragraphs
        desc_paragraphs = [None]
        for p in raw_desc.split('\n'):
            if len(p.split(' ')) <= 3:
                if desc_paragraphs[-1]:
                    desc_paragraphs[-1] += ' ' + p
                else:
                    desc_paragraphs[-1] = p
            else:
                if desc_paragraphs[-1]:
                    desc_paragraphs.append(p)
                else:
                    desc_paragraphs[-1] = p
                    desc_paragraphs.append(None)
        if not desc_paragraphs[-1]:
            desc_paragraphs.pop()

        # Add to data
        for p in desc_paragraphs:
            data.append(make_entry(p, head='DOCUMENT DESCRIPTION'))

        ## Abstract ##
        abstract = soup.find('abstract')
        if abstract:
            abstract_raw = ''
            for p in abstract.find_all():
                abstract_raw += ' ' + p.text
            abstract_raw = tokenize(abstract_raw)
            data.append(make_entry(abstract_raw, head='ABSTRACT'))

        ## Main Body ##
        position = 0
        body = soup.find('text').find('body')
        for div in body.find_all('div', recursive=False):
            head = ''
            for h in div.find_all('head'):
                head += ' ' + h.text

            for p in div.find_all('p'):
                ptext = p.text
                data.append(make_entry(tokenize(ptext), head=head.strip(
                ), position='Paragraph {}'.format(position)))
                position += 1

        data = pd.DataFrame(data)
        return data

# ----- Filtering ----- #


def filter(data):
    par_min_len = 25
    par_max_len = 300

    # Constraints
    constraints = [
        lambda s: par_min_len <= len(
            s.split(' ')) <= par_max_len  # Length Constraint
    ]

    # Exceptions
    exceptions = [
        lambda s: s.lower().startswith('abstract')  # Abstract exception
    ]

    # Non description based constraints
    no_abstract_locs = (data['head'].apply(
        lambda s: s.strip().lower()) != 'abstract')
    no_discussion_locs = (data['head'].apply(
        lambda s: 'discussion' not in s.strip().lower()))

    def should_include(s): return all(f(s)
                                      for f in constraints) or any(f(s) for f in exceptions)
    include_locs = data['description'].apply(
        should_include) & no_abstract_locs & no_discussion_locs

    return data[include_locs]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Parse directory of GROBID-generated XML documents.')
    parser.add_argument(
        'dir', type=str, help='Directory of XMLs to be used to create annotation tasks.')
    parser.add_argument('output_dir', type=str,
                        help='Path to directory where annotation tasks are to be placed.')
    parser.add_argument('--no-filter', action='store_true',
                        default=False, help='Do not filter extracted paragraphs.')

    def construct_task_cli(args):
        # Parsing
        dfs = [parse_xml(os.path.join(args.dir, fname))
               for fname in os.listdir(args.dir)]
        data = pd.concat(dfs)

        # Filtering
        if not args.no_filter:
            data = filter(data)

        # Save Results
        data.to_csv(os.path.join(args.output_dir, 'tasks.csv'), index=False, quoting=csv.QUOTE_ALL)

    args = parser.parse_args()

    print(f'Constructing tasks from XMLs located in {args.dir} and placing it in {args.output_dir}')
    construct_task_cli(args)
