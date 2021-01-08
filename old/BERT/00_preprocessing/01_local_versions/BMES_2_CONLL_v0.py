import tqdm
import codecs
import itertools
import pandas as pd

input_path = 'C:\\Users\\siban\\Dropbox\\CSAIL\\Projects\\02_Github\\takeda_nlp\\00_data\\01_BMES\\BMES_merged'
output_path = 'C:\\Users\\siban\\Dropbox\\CSAIL\\Projects\\02_Github\\takeda_nlp\\00_data\\02_CONLL\\CONLL_merged'

tokens = []
tags_BMES = []
tags_CONLL = []

with codecs.open(input_path, 'r', 'utf-8') as fr:
    file_lines = fr.readlines()
    
    for i, line in tqdm.tqdm(enumerate(file_lines), total = len(file_lines)):
        line = line.strip('\n').strip()
        if line == '':
            tokens.append('')
            tags_BMES.append('')
            continue
        
        else:
            token = line.split(' ')[0]
            tag_BMES = line.split(' ')[1]
            tokens.append(token)
            tags_BMES.append(tag_BMES)            
    
for tag_BMES in tags_BMES:
    
    if tag_BMES == '':
        tag_CONLL = ''
    
    elif tag_BMES[0] == 'O':
        tag_CONLL = 'O'
    
    else:
        prefix = tag_BMES.split('-')[0]
        tag = tag_BMES.split('-')[1]
        
        if prefix == 'B':
            tag_CONLL = 'B' + '-' + tag
    
        if prefix == 'I':
            tag_CONLL = 'I' + '-' + tag
            
        if prefix == 'E':
            tag_CONLL = 'I' + '-' + tag
            
        if prefix == 'S':
            tag_CONLL = 'B' + '-' + tag

    tags_CONLL.append(tag_CONLL)
        
print(pd.value_counts(tags_BMES))
print(pd.value_counts(tags_CONLL))
print('# tokens =', len(tokens))
print('# tags_BMES =', len(tags_BMES))      
print('# tags_CONLL =', len(tags_CONLL))      

with codecs.open(output_path, 'w', 'utf-8') as fw:
    for token, tag_CONLL in zip(tokens, tags_CONLL):
        fw.write(token + '\t' + tag_CONLL + '\n')
        
# Split by spaces:
# aux = [list(group) for k, group in itertools.groupby(tokens, lambda x: x == '') if not k]        
