'''
Match annotations to original struct. The goal of this script is to (1) recover document name from id. (2) Identify which arm a given annotation belongs to.
'''

import os
import argparse
import json
from bisect import bisect_left, bisect_right

defaults_ignore_labs = {
    'title'
}


def match_paragraphs(pair, lab_ignore=defaults_ignore_labs):
    original, corrected = pair

    # Ensure paragraphs match
    assert(original['text'] == corrected['text'])

    # Create location -> arm mapping
    labs = [p[:-6] for p in original.keys() if p.endswith('-spans')
            and p[:-6] not in lab_ignore]

    arm_map = dict()
    for l in labs:
        spans = original[f'{l}-spans']
        arms = original[f'{l}-arms']
        for a, rng in zip(arms, spans):
            arm_map[tuple(rng)] = a

    # Sort by start and then end
    ranges = list(arm_map.keys())
    ranges.sort(key=lambda p: p[1])
    ranges.sort(key=lambda p: p[0])

    if len(ranges) == 0:
        # no annotations, return plain text
        return corrected

    starts, stops = zip(*ranges)

    clabs = [p[:-6] for p in corrected.keys() if p.endswith('-spans')
             and p[:-6] not in lab_ignore]

    for lab in clabs:
        span_key = f'{lab}-spans'
        arm_key = f'{lab}-arms'
        for j, rng in enumerate(corrected[span_key]):
            if not arm_key in corrected:
                corrected[arm_key] = []

            if not lab.lower().startswith('arm_'):
                # non-arm entities get arm "-1" to represent all arms should get it
                corrected[arm_key].append(-1)

            else:
                start, stop = rng
                start_idx = bisect_right(stops, start)
                stop_idx = bisect_right(starts, stop)

                # Find range with greatest overlap
                idx = -1
                frac_match = -1
                for i in range(start_idx, stop_idx):
                    s, t = ranges[i]
                    overlap_start = max(s, start)
                    overlap_stop = min(t, stop)
                    size = overlap_stop - overlap_start
                    frac = size/(stop - start)

                    if frac > frac_match:
                        idx = i
                        frac_match = frac

                # arm of annotation w/ greatest overlap
                if frac_match > 0:
                    corrected[arm_key].append(arm_map[ranges[idx]])
                else:
                    # if no match, use for all arms
                    corrected[arm_key].append(-1)

    return corrected


def match_annotations(original_path, corrected_path, matched_path):

    original_path = os.path.normpath(original_path)
    original_path = os.path.realpath(original_path)
    with open(original_path, 'r') as f:
        original = json.load(f)

    corrected_path = os.path.normpath(corrected_path)
    corrected_path = os.path.realpath(corrected_path)
    with open(corrected_path, 'r') as f:
        corrected = json.load(f)

    output_dict = {}

    for doc_id in corrected:
        corrected_dict = corrected[doc_id]

        if doc_id not in original:
            print(f'Unable to find original entry for document: {doc_id}')
            continue

        original_dict = original[doc_id]

        # Recover document name
        corrected_dict['doc_name'] = original_dict['doc_name']

        # Assert paragraphs match
        corr_pars = [p['text'] for p in corrected_dict['paragraphs']]
        orig_pars = [p['text'] for p in original_dict['paragraphs']]
        assert(corr_pars == orig_pars)

        paragraph_pairs = zip(
            original_dict['paragraphs'], corrected_dict['paragraphs'])

        pars = []
        for pair in paragraph_pairs:
            matched = match_paragraphs(pair)
            pars.append(matched)

        corrected_dict['paragraphs'] = pars
        output_dict[doc_id] = corrected_dict
    
    with open(matched_path, 'w') as f:
        json.dump(output_dict, f, indent=4)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('original_struct_path', type=str,
                        help='Path to original struct.')
    parser.add_argument('corrected_struct_path', type=str,
                        help='Path to corrected struct.')
    parser.add_argument('--matched_path', type=str,
                        help='Path where matched struct should be saved.', default=None)
    parser.add_argument('--in_place', action='store_true', default=False,
                        help='If passed, the matched struct will be saved in the file of the corrected struct.')

    args = parser.parse_args()

    if not args.matched_path and not args.in_place:
        raise Exception('Please enter output location or pass --in_place.')

    if args.in_place:
        outpath = args.corrected_struct_path
    else:
        outpath = args.matched_path

    match_annotations(args.original_struct_path, args.corrected_struct_path, outpath)
