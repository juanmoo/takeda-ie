# Data Processing Module
## Description
This module provides a toolkit to process document data prior to be used by the modeling module.

## Data Format
The modeling module assumes that all data presented comes is in the STRUCT format. The basic information contained within a struct is listed below.

STRUCT-base:
```json
[
    'document_id': {
        'document_id': <UUID>,
        'file_name': <str>,
        'title': <str>,
        'file_name': <str>,
        'paragraphs': [
            {
                'text': <str>,
                'header': <str>,
                'location': <str>
            },
            ...
        ]
    },
    ...
]
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
2. ``output_path``: Path to outpu of JSON struct file.

#### Example: 
```bash
python <path to cli.py> --num_workers=1 <path-to-xml-dir> <path-to-output-dir>/struct.json
```
