'''
Main entry point to use processing CLI.
'''

import argparse
import os
import parse
import annotate
import split
import table

# Parsing CLI wrapper


def xml_parse_cli(args):
    # Normalize Paths
    input_dir = os.path.normpath(args.input_dir)
    input_dir = os.path.realpath(input_dir)

    output_path = os.path.normpath(args.output_path)
    output_path = os.path.realpath(output_path)

    kwargs = vars(args)
    kwargs['input_dir'] = input_dir
    kwargs['output_file'] = output_path

    parse.batch_process(**kwargs)

# Annotate CLI wrapper


def new_annotation_cli(args):
    struct_path = os.path.normpath(args.struct_path)
    struct_path = os.path.realpath(struct_path)

    output_path = os.path.normpath(args.output_path)
    output_path = os.path.realpath(output_path)

    kwargs = vars(args)
    kwargs['struct_path'] = struct_path
    kwargs['output_path'] = output_path
    annotate.create_annotation_tasks(**kwargs)

# Split Struct CLI


def split_cli(args):
    struct_path = os.path.normpath(args.struct_path)
    struct_path = os.path.realpath(struct_path)

    output_dir = os.path.normpath(args.output_dir)
    output_dir = os.path.realpath(output_dir)

    kwargs = vars(args)
    kwargs['struct_path'] = struct_path
    kwargs['output_dir'] = output_dir

    split.split_struct(**kwargs)

# Make Table CLI


def make_table_cli(args):
    struct_path = os.path.normpath(args.struct_path)
    struct_path = os.path.realpath(struct_path)

    output_path = os.path.normpath(args.output_path)
    output_path = os.path.realpath(output_path)

    kwargs = vars(args)
    kwargs['struct_path'] = struct_path
    kwargs['output_path'] = output_path

    table.create_table(**kwargs)


def load_annotations_cli(args):
    input_struct = os.path.normpath(args.input_struct)
    input_struct = os.path.realpath(input_struct)

    annotations_path = os.path.normpath(args.annotations_path)
    annotations_path = os.path.realpath(annotations_path)

    output_struct = os.path.normpath(args.output_struct)
    output_struct = os.path.realpath(output_struct)

    kwargs = vars(args)
    kwargs['input_struct'] = input_struct
    kwargs['annotations_path'] = annotations_path
    kwargs['output_struct'] = output_struct

    annotate.load_annotations(**kwargs)



if __name__ == '__main__':
    # Main Parser
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='sub-command help')
    # Main Optional Arguments
    parser.add_argument('--num_workers', type=int, default=1)

    # XML Parser
    xml_parser = subparsers.add_parser('xml_parse', help='Parse GROBID XMLs')
    xml_parser.add_argument('input_dir', type=str,
                            help='Directory with GROBID XML files.')
    xml_parser.add_argument('output_path', type=str,
                            help='Path of output JSON struct file.')
    xml_parser.set_defaults(handler=xml_parse_cli)

    # Annotation File Parser
    new_annotation_parser = subparsers.add_parser(
        'create_annotations', help='Create annotation tasks from JSON struct file')
    new_annotation_parser.add_argument(
        'struct_path', type=str, help='Path to JSON struct file.')
    new_annotation_parser.add_argument(
        'output_path', type=str, help='Path to annotation output file.')
    new_annotation_parser.add_argument('--min_par_length', type=int, default=25,
                                       help='Minimum length of paragraphs to be considered.')
    new_annotation_parser.add_argument('--max_par_length', type=int, default=300,
                                       help='Maximum length of paragraphs to be considered.')

    new_annotation_parser.set_defaults(handler=new_annotation_cli)

    # Split Parser
    split_parser = subparsers.add_parser(
        'split', help='Create Train/Test splits')
    split_parser.add_argument('struct_path', type=str,
                              help='Path to JSON struct.')
    split_parser.add_argument('output_dir', type=str,
                              help='Path to output directory.')
    split_parser.add_argument('--test_frac', type=float, default=0.2,
                              help='Fraction of paragraphs to use in test split.')
    split_parser.add_argument('--paragraph_split', default=False, action='store_true',
                              help='Create split paragraph-wise. By default, splits are made document-wise.')
    split_parser.set_defaults(handler=split_cli)

    # Make Table Parser
    table_parser = subparsers.add_parser(
        'make_table', help='Create summary table from struct.')
    table_parser.add_argument('struct_path', type=str,
                              help='Path to JSON struct.')
    table_parser.add_argument('output_path', type=str,
                              help='Path to output spreadsheet.')
    table_parser.set_defaults(handler=make_table_cli)

    # Load Annotations Parser
    load_parser = subparsers.add_parser(
        'load_annotations', help='Load annotation file into struct.')
    load_parser.add_argument('input_struct', type=str,
                             help='Path to JSON struct.')
    load_parser.add_argument('annotations_path', type=str,
                             help='Path to annotations CSV file.')
    load_parser.add_argument('output_struct', type=str,
                              help='Path to output annotated struct.')
    load_parser.set_defaults(handler=load_annotations_cli)
    

    # Parse and Execute handler function
    args = parser.parse_args()
    args.handler(args)
