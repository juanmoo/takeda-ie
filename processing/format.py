'''
Host logic to transform datasets from one format into another.
'''

# -- BIO -- #
def struct_to_bio(struct, task='ner', label_map={}, **kwargs):

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


# if __name__ == '__main__':
#     import json
#     infile = '/Users/juanmoo/Desktop/changed.json'
#     outfile = '/Users/juanmoo/Desktop/stuff.json'

#     struct = json.load(open(infile, 'r'))
#     out = struct_to_bio(struct)
#     json.dump(out, open(outfile, 'w'), indent=4)
