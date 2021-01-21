# Takeda - MIT Medical Trial Extraction Project
This repository contains code/data for extracting named entities from scientific literature.

<!-- ## Installation -->
<!-- TODO: Prune dependency list and create a requirements/conda reqs  -->

## Usage
The code in this repository is structured to be used either programatically or through the available CLI. To utilize the available functions using the command line interface (CLI), the entry point at ``medtrialext/main.py`` will be used.

The current available commands are as follows:


| Command | Function |
| ---- | ---- |
| xml_to_struct | Parse GROBID xmls |
| read_annotations | Read annotations file. |
| create_ner_bio | Create NER BIO annotations. |
| create_rd_bio | Create RD BIO annotations. | 
| train | Train models from annotations. | 
| pred | Make predictions using models and annotations. |
| create_table  | Generate summary table from NER and RD predictions. |

<!-- ## Performace -->
<!-- TODO: Table w/ per task perf -->