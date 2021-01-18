# Data Processing Module
## Description
This module provides a toolkit to process document data prior to be used by the modeling module.

## Data Format
The modeling module assumes that all data presented comes is in the STRUCT format. The basic information contained within a struct is listed below.

STRUCT-base:
```json
{
    'documents': [
        'document_id': {
            'document_id': <UUID>,
            'file_name': <str>,
            'title': <str>,
            'authors': [<str>, ...]
            'paragraphs': [
                {
                    'text': <str>,
                    'header': <str>,
                    'location': <str>,
                    'annotated': <boolean>,
                },
                ...
            ]
        },
        ...
    ],
    'ner_evals': [
        {
            'precision': <float>,
            'recall': <float>,
            'f1': <float>,
        }, ...
    ],
    'ner_metadata': [
        {
            'architecture': 'bert',
            'model_dir': <str-path>,
            'task': 'ner' or 'rd',
            'oversampling_rate': <int>
        }, ...
    ],
    'ner_preds': [
        {
            'document_id': [
                {
                    'toks': [<str>, ...],
                    'tags': [<str>, ...],
                    'spans': {
                        <key-str>: [(<int>, <int>), ...]
                    }
                }
            ]
        }
    ],
    'rd_evals': [{...}] ,
    'ner_metadata': [{...}] ,
    'ner_preds': [{...}],
}
```

## Usage
For ease of use, the toolkit implemented in this module is accessed in the form of a command line interface (CLI).

### General Optional Arguments
* ``--num_workers``: Number of maximum threads to be used. Default is 1.

### XMLs to STRUCT-base
Currently, the only supported raw input format is GROBID XMLs. In order to create them, please follow the instructions in the [tool's documentation](https://grobid.readthedocs.io/en/latest/) to download, install, and run GROBID to parse native PDFs to GROBID XMLs.

#### Arguments:
Command: xml_parse

Positional: 
1. ``input_dir``: Directory with Grobid XML files.
2. ``output_path``: Path to output of JSON struct file.

#### Example: 
```bash
python <path to cli.py> --num_workers=1 xml_parse <path-to-xml-dir> <path-to-output-dir>/struct.json
```

### Create Annotations
#### Arguments:
Command: create_annotations

Positional: 
1. ``struct_path``: Path to JSON struct file.
2. ``output_path``: Path to annotation output file.

Optional:
1. ``--min_par_length``: Minimum length of paragraphs to be considered (default: 25).
2. ``--max_par_length``: Maximum length of paragraphs to be considered (default: 300).

#### Example: 
```bash
python <path to cli.py> --num_workers=1 <path-to-xml-dir> <path-to-output-dir>/tasks.csv
```

### Train/Test Split
#### Arguments:
Command: split

Positional:
1. ``struct_path``: Path to JSON struct.
2. ``output_dir``: Path to output directory.

Optional:
1. ``--test_frac``: Fraction of paragraphs to use in test split.
2. ``--paragraph_split``: Boolean flag. If given, train/test split will be done at the paragraph level.

### Create Summary Table
#### Arguments:
Command: make_table

Positional:
1. ``struct_path``: Path to JSON struct.
2. ``output_path``: Path to output spreadsheet.