'''
BERT NER Driver Module
'''
# Get file's directory to use bash scripts and relative imports.
import os
from re import sub
import sys
dir_path = os.path.dirname(os.path.realpath(__file__))
project_root = '/'.join(dir_path.split('/')[:-4])
sys.path.append(project_root)


# Imports
import subprocess
import tempfile

# Relative Imports
from processing import format

### Training ###

def train(struct, output_model_dir, **kwargs):

    # Default GPU settings
    gpus = kwargs.get('gpus', "0")

    # Create BIO annotation files
    bio_dict = format.struct_to_bio(struct, task='ner', **kwargs)
    data_dir = tempfile.TemporaryDirectory()
    data_dir_path = data_dir.name
    train_file_path = os.path.join(data_dir_path, 'train.txt')

    train_txts = []
    for doc_id in bio_dict:
        pars = bio_dict[doc_id]
        train_txts.extend(pars)

    with open(train_file_path, 'w') as bio_file:
        out = '\n\n'.join(train_txts)
        bio_file.write(out)
    
    # Train 
    output_dir = tempfile.TemporaryDirectory()
    output_dir_path = output_dir.name
    train_cmd = os.path.join(dir_path, 'BERT', 'train.sh')
    cmd = ['/bin/bash', train_cmd, data_dir_path, output_dir_path, gpus]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, _ = proc.communicate()

    cmd2 = ['mv', output_dir_path, '/Users/juanmoo/Desktop/']
    proc = subprocess.run(cmd2)

    print(stdout)
    



    

    
    

if __name__ == '__main__':
    import json
    output_model_dir = '/Users/juanmoo/Desktop/model/'
    with open('/Users/juanmoo/Desktop/changed.json', 'r') as f:
        struct = json.load(f)
        train(struct, output_model_dir)
