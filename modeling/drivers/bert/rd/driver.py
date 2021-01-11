'''
BERT NER Driver Module
'''
# Get file's directory to use bash scripts and relative imports.
import os
from re import sub
import sys
import json
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

    struct = json.load(open(struct, 'r'))

    # Default GPU settings
    gpus = kwargs.get('gpus', "0,1,2,3,4,5,6,7")

    tmp_dir = tempfile.TemporaryDirectory()

    # Create BIO annotation files
    kwargs['task'] = 'rd'
    bio_dict = format.struct_to_bio(struct, **kwargs)
    data_dir = os.path.join(tmp_dir.name, 'data_dir')
    os.makedirs(data_dir, exist_ok=True)
    data_dir_path = data_dir
    train_file_path = os.path.join(data_dir_path, 'train.txt')

    train_txts = []
    for doc_id in bio_dict:
        pars = bio_dict[doc_id]
        train_txts.extend(pars)

    with open(train_file_path, 'w') as bio_file:
        out = '\n\n'.join(train_txts)
        bio_file.write(out)

    # Train
    output_dir = os.path.join(tmp_dir.name, 'output_dir')
    os.makedirs(output_dir, exist_ok=True)
    output_dir_path = output_dir
    train_cmd = os.path.join(dir_path, 'BERT', 'train.sh')
    cmd = ['/bin/bash', train_cmd, data_dir_path, output_dir_path, gpus]
    print(' '.join(cmd))
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, _ = proc.communicate()

    cmd2 = ['mv', output_dir_path, output_model_dir]
    proc = subprocess.run(cmd2)

    print(stdout)



if __name__ == '__main__':
    import json
    output_model_dir = '/data/rsg/nlp/juanmoo1/projects/02_takeda_dev/00_takeda/tmp/model'
    struct_path = '/data/rsg/nlp/juanmoo1/projects/02_takeda_dev/00_takeda/tmp/changed.json'
    with open(struct_path, 'r') as f:
        struct = json.load(f)
        train(struct, output_model_dir)
