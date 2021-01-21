'''
Main CLI interface
'''

import argparse
import formatting

# Main Parser
parser = argparse.ArgumentParser()
subparser = parser.add_subparsers(help='sub-command help')

# XMLs -> Struct
xml_parser = subparser.add_parser('xml_to_struct', help='Parse GROBID xmls')
xml_parser.add_argument('xml_dir', type=str, help='Path to directory with GROBID xmls')
xml_parser.add_argument('output_path', type=str, help='Output path.')
xml_parser.add_argument('--num_workers', type=int, default=1, help='Maximum number of threads to use.')

xml_parser.set_defaults(handler=formatting.xml_batch_process_cli)

# Read annotations
read_ann_parser = subparser.add_parser('read_annotations', help='Read annotations file.')
read_ann_parser.add_argument('annotation_file_path', type=str, help='Path to annotation files.')
read_ann_parser.add_argument('struct_base_path', type=str, help='Path to base struct file.')
read_ann_parser.add_argument('--struct_annotated_path', type=str, default=None, help='Path to save annotated struct file. If not given, annotation will be done in-place.')
read_ann_parser.add_argument('--match_ids_by_filename', default=False, action='store_true', help='Correct document ids from struct using file names in the annotation.')
read_ann_parser.add_argument('--verbose', default=False, action='store_true', help='Enable verbose output.')
read_ann_parser.add_argument('--num_workers', type=int, default=1, help='Maximum number of threads to use.')

read_ann_parser.set_defaults(handler=formatting.read_annotations)

# Create NER BIO Annotations
ner_bio_parser = subparser.add_parser('create_ner_bio', help='Create NER BIO annotations.')
ner_bio_parser.add_argument('struct_ann_path', type=str, help='Path to annotated struct')
ner_bio_parser.add_argument('output_dir', type=str, help='Path to directory where BIO annotations should be placed')

ner_bio_parser.add_argument('--oversampling_rate', type=int, default=1, help='Oversampling rate to be used.')
ner_bio_parser.add_argument('--separate_docs', default=False, action='store_true', help='Output separate documents.')
ner_bio_parser.set_defaults(handler=formatting.struct_to_bio)

# Create RD BIO Annotations
rd_bio_parser = subparser.add_parser('create_rd_bio', help='Create RD BIO annotations.')
rd_bio_parser.add_argument('struct_ann_path', type=str, help='Path to annotated struct')
rd_bio_parser.add_argument('output_dir', type=str, help='Path to directory where BIO annotations should be placed')

rd_bio_parser.add_argument('--separate_docs', default=False, action='store_true', help='Output separate documents.')
rd_bio_parser.set_defaults(handler=formatting.struct_to_bio_rd)


if __name__ == '__main__':

    # parse and execute
    args = parser.parse_args()
    args.handler(args)