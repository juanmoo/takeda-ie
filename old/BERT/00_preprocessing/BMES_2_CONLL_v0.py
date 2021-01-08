import tqdm
import codecs
import argparse
import pandas as pd

def main(input_path, output_path):
    tokens = []
    tags_BMES = []
    tags_CONLL = []
    
    with codecs.open(input_path, mode = 'r', encoding = 'utf-8', errors ='replace') as fr:
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
            if token == '':
                fw.write('\n')
            else:
                fw.write(token + '\t' + tag_CONLL + '\n')
 
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("input_path", type=str, help="Path to input BMES file")
    parser.add_argument("output_path", type=str, help="Path to output CONLL file")

    args = parser.parse_args()
    
    main(args.input_path, args.output_path)
        
# Split by spaces to check paragraph length:
# aux = [list(group) for k, group in itertools.groupby(tokens, lambda x: x == '') if not k]        
