'''
Script to interactively merge BMES annotations.
'''
import re
import argparse
import os


def check_matches(labels):
    current_lab = ''
    current_start = -1

    for j, l in enumerate(labels):
        if current_lab != '':
            if l not in [f'E-{current_lab}', f'M-{current_lab}']: # didn't finish label
                raise Exception(f'Unable to match {current_lab} in line {current_start}. Failed in line {j}')
            elif l == f'M-{current_lab}':
                continue
            elif l == f'E-{current_lab}':
                current_lab = ''
                current_start = -1
        else:
            if l == 'O':
                continue
            elif not('B-' in l or 'S-' in l):
                raise Exception(f'Unmatched {l} found in line {j}.')
            else:
                t, lab = l.split('-')
                if t == 'S':
                    continue
                elif t == 'B':
                    current_lab = lab
                    current_start = j
                else:
                    raise Exception(f'Unknown tag type {t}')
    print('\nLabel Assignment is Valid!\n\n')
    return True
            

# Currently, this function iterates through the document and finds sequences of singleton tags
# and gives the option of merging them.
def correct_bmes_document(input_path, output_dir):
    with open(input_path, 'r') as f:
        text = f.read()
    tokens, labels = zip(*[re.sub('\s+', ' ', l.strip()).split()
                           for l in text.split('\n')])
    labels = list(labels)
    # Verify label integrity
    check_matches(labels)

    i = j = 0

    while i < len(labels):
        # Skip forward until S-* found
        while i < len(labels) and not labels[i].startswith('S-'):
            i += 1
        
        # S-* series not found
        if not i < len(labels):
            break

        else:
            j = i
            # Skip forward until S-* no longer found
            while j < len(labels) and labels[j] == labels[i]:
                j += 1
            
            if j - i > 1: # Series of labels encountered
                print('-' * 50)
                print('Should the following tokens be merged? (y or n)')
                for k in range(i, j):
                    print('-', tokens[k], '||', labels[k])
                ans = input('')
                while ans.lower() not in ['y', 'n']:
                    ans = input('Try again.\n')
                if ans.lower() == 'y':
                    lab = labels[i].split('-')[0]
                    labels[i] = f'B-{lab}'
                    labels[j - 1] = f'E-{lab}'
                    for k in range(i + 1, j - 1):
                        labels[k] = f'M-{lab}'
            
            i = j
    lines = zip(tokens, labels)
    output = ''
    for l in lines:
        output += ' '.join(l) + '\n'
    output = output[:-1]

    basename = os.path.basename(input_path)

    with open(os.path.join(output_dir, basename), 'w') as f:
        f.write(output)
    



if __name__ == '__main__':
    parser = argparse.ArgumentParser('<script>')
    parser.add_argument('input_dir', type=str,
                        help='Path to bmes file to correct.')
    parser.add_argument('output_dir', type=str,
                        help='Path to output directory.')

    def correct_cli(args):
        files = [f for f in os.listdir(args.input_dir) if f.lower().endswith('.bmes')]
        for f in files:
            print(f'\n\n{"=" * 100}\nProcessing document: \'{f}\'\n')
            correct_bmes_document(os.path.join(args.input_dir, f), args.output_dir)

    args = parser.parse_args()
    correct_cli(args)
