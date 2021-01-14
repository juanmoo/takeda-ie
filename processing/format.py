'''
Host logic to transform datasets from one format into another.
'''
import json
import os
from tqdm import tqdm
from spacy.lang.en import English

# -- BIO -- #
def struct_to_bio(struct, task, label_map={}, **kwargs):
    if task == 'ner':
        return struct_to_ner_bio(struct, label_map=label_map, **kwargs)
    elif task == 'rd':
        return struct_to_rd_bio(struct, label_map=label_map, **kwargs)


def struct_to_ner_bio(struct, label_map={}, **kwargs):
    doc_structs = struct['documents']
    fnames = doc_structs.keys()
    bmes_list = []
    for fname in fnames:
        paragraphs_bmes = []
        for entry in doc_structs[fname]['paragraphs']:

            if entry['annotated'] == False:
                continue

            text = entry['text']
            bmes_tokens = text.split()
            bmes_annotations = ['O |'] * len(bmes_tokens)

            lmin = None
            lmax = None
            for k in [e for e in entry.keys() if e.startswith('ann-') and e.endswith('-spans') and 'title' not in e]:
                key = k[4:-6]
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

            if all_merged != True:
                raise Exception('Found overlapping annotations.')

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

# Empty NER
def struct_to_bio_empty(struct, **kwargs):
    doc_structs = struct['documents']
    output = dict()

    for doc_id in doc_structs:
        doc_struct = doc_structs[doc_id]
        doc_pars = []

        for par in doc_struct['paragraphs']:
            text = par['text']
            tokens = text.strip().split(' ')
            par_text = '\n'.join(tokens)
            doc_pars.append(par_text)
        
        doc_text = '\n\n'.join(doc_pars)
        output[doc_id] = doc_text
    
    return output


## RD ####
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

def process_document(doc_struct, foi=default_foi, trigger=default_trigger, use_sent=False, window=1):
    data = []
    trigger_span_key = f'ann-{trigger}-spans'
    trigger_arm_key = f'ann-{trigger}-arms'

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

            tagged_text = []
            for token in tokens:
                tagged_text.append([token, 'O'])

            # assign B/I- tags to each token
            for field in foi:
                field_span_key = f'ann-{field}-spans'
                field_arm_key = f'ann-{field}-arms'

                if not field_span_key in par:
                    # print(f'{field_span_key} not found. Skipping!')
                    continue

                fval_spans = par[field_span_key]
                fval_arms = par[field_arm_key]

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

            if use_sent:
                seg_start, seg_end = get_segment(span, sent_boundaries, window=window)
                tagged_segment = tagged_text[seg_start:(seg_end+2)]
            else:
                tagged_segment = tagged_text

            data.append(tagged_segment)

    bio_pars = ['\n'.join(['{}\t{}'.format(t, l) for (t, l) in par_toks]) for par_toks in data]

    return bio_pars

def struct_to_rd_bio(struct, label_map={}, use_scent=False, **kwargs):
    doc_structs = struct['documents']
    output = dict()

    for doc_id in doc_structs:
        output[doc_id] = process_document(doc_structs[doc_id], use_sent=use_scent)

    return output

def process_document_rd_blank(doc_struct, preds, foi=default_foi, trigger=default_trigger, use_ner_preds=True, use_sent=False, window=1):
    data = []

    for par, pred in zip(doc_struct['paragraphs'], preds):
        pred = pred['spans']

        # Skip paragraphs w/o trigger entities

        if trigger not in pred or len(pred[trigger]) == 0:
            continue

        text = par['text']
        tokens = text.strip().split(' ')
        sentences = get_sentences(text)

        sent_boundaries = [0]
        for sent in sentences:
            sent_boundaries.append(
                len(sent.strip().split(' ')) + sent_boundaries[-1])

        for span in pred[trigger]:

            # copy tokens
            tagged_text = list(tokens)

            desc_span_start, desc_span_end = span
            tagged_text.insert(desc_span_start, "[P1]")
            tagged_text.insert(desc_span_end + 1, "[P2]")

            if use_sent:
                seg_start, seg_end = get_segment(span, sent_boundaries, window=window)
                tagged_segment = tagged_text[seg_start:(seg_end+2)]
            else:
                tagged_segment = tagged_text

            data.append(tagged_segment)

    bio_pars = ['\n'.join(par_toks) for par_toks in data]
    doc_bio = '\n\n'.join(bio_pars)

    return doc_bio

def struct_to_rd_bio_empty(struct, label_map={}, use_scent=False, use_ner_preds=True, **kwargs):
    doc_structs = struct['documents']
    output = dict()

    for doc_id in doc_structs:
        doc_preds = struct['ner_preds'][-1][doc_id]
        output[doc_id] = process_document_rd_blank(doc_structs[doc_id], doc_preds, use_ner_preds=use_ner_preds, use_sent=use_scent)

    return output

# Utils #
def make_spans(tags, all_labels=set()):
    labels = set() | all_labels

    spans = {k:[] for k in labels}

    i = 0
    while i < len(tags):
        # skip all irrelevant tags
        while i < len(tags) and tags[i][2:] not in labels:
            i += 1

        if i >= len(tags):
            break
        
        # Find end of span
        current_tag = tags[i][2:]
        assert(current_tag in spans)

        j = i + 1
        while j < len(tags) and tags[j].endswith(current_tag) and (not tags[j].startswith('B-')):
            j += 1
        spans[current_tag].append((i, j))

        i = j
    return spans


# if __name__ == '__main__':
#     import json

#     infile = '/data/rsg/nlp/juanmoo1/projects/02_takeda_dev/00_takeda/tmp/struct.json'
#     out_dir = '/data/rsg/nlp/juanmoo1/projects/02_takeda_dev/00_takeda/tmp/test/'

#     struct = json.load(open(infile, 'r'))
#     rd_out = struct_to_bio_empty(struct)

#     for doc_id in rd_out:
#         fname = os.path.join(out_dir, doc_id + '.bio')
#         with open(fname, 'w') as ofile:
#             ofile.write(rd_out[doc_id])
