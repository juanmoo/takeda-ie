'''
Logic to create summary table from NER & RD predictions and document metadata.
'''

import json
import pandas as pd

def create_table(struct_path, output_path, **kwargs):

    # Read predictions
    struct = None
    with open(struct_path, 'r') as struct_file:
        struct = json.load(struct_file)

    rd_preds = struct['rd_preds'][-1]
    ner_preds = struct['ner_preds'][-1]

    document_ids = list(set(ner_preds.keys()) | set(rd_preds.keys()))
    document_ids.sort()

    # Get NER entities
    ner_entities = {id: [] for id in document_ids}
    for doc_id in document_ids:
        if doc_id not in ner_preds:
            continue

        doc_ner_preds = ner_preds[doc_id]

        for ner_pred in doc_ner_preds:
            par_ents = dict()
            ent_count = 0
            for ent_key in ner_pred['spans']:
                par_ents[ent_key] = []
                for start, stop in ner_pred['spans'][ent_key]:
                    toks = ner_pred['toks'][start:stop]
                    ent = ' '.join(toks)
                    par_ents[ent_key].append(ent)
                    ent_count += 1
            if ent_count > 0:
                ner_entities[doc_id].append(par_ents)

    # Get RD entities
    rd_entities = {id: [] for id in document_ids}
    for doc_id in document_ids:
        if doc_id not in rd_preds:
            continue

        doc_rd_preds = rd_preds[doc_id]

        for rd_par_preds in doc_rd_preds:
            for desc_pred in rd_par_preds:
                par_ents = dict()
                ent_count = 0
                for ent_key in desc_pred['spans']:
                    par_ents[ent_key] = []
                    for start, stop in desc_pred['spans'][ent_key]:
                        toks = desc_pred['toks'][start:stop]
                        ent = ' '.join(toks)
                        par_ents[ent_key].append(ent)
                        ent_count += 1
                    par_ents[ent_key] = ' | '.join(par_ents[ent_key])

                # Add Arm Descriptor
                try:
                    desc_start = desc_pred['toks'].index('[P1]')
                    desc_stop = desc_pred['toks'].index('[P2]')
                    par_ents['arm_description'] = ' '.join(
                        desc_pred['toks'][desc_start + 1:desc_stop])
                    if ent_count > 1:
                        rd_entities[doc_id].append(par_ents)
                except:
                    pass

    # Create Table
    dfs = []
    target_cols = ['document_id', 'document_name', 'title', 'authors', 'study_type',
                   'arm_description', 'arm_dosage', 'arm_efficacy_metric', 'arm_efficacy_results']
    for doc_id in rd_entities:

        if doc_id not in rd_entities:
            continue

        doc_ents = rd_entities[doc_id]
        doc_df = pd.DataFrame(doc_ents)
        for col in target_cols:
            if col not in doc_df:
                doc_df[col] = ''
        doc_df = doc_df[target_cols]

        # Place non-arm information in the first line
        authors = struct['documents'][doc_id]['authors'][:5]
        study_type = ['placeholder']
        doc_name = struct['documents'][doc_id]['file_name']
        title = struct['documents'][doc_id]['title']

        if len(doc_df) > 0:
            doc_df.iloc[0]['authors'] = ' || '.join(authors)
            doc_df.iloc[0]['study_type'] = ' || '.join(study_type)
            doc_df.iloc[0]['document_id'] = doc_id
            doc_df.iloc[0]['document_name'] = doc_name
            doc_df.iloc[0]['title'] = title
        else:
            doc_df.append({
                'authors': ' || '.join(authors),
                'study_type': ' || '.join(study_type),
                'document_id': doc_id,
                'document_name': doc_name,
                'title': title
            }, ignore_index=True)
        dfs.append(doc_df)

    df = pd.concat(dfs)
    # Colum Renames
    rename_map = {'document_id': 'Document ID', 'document_name': 'File Name', 'title': 'Title', 'authors': 'Authors', 'study_type': 'Study Type',
                  'arm_description': 'Description', 'arm_dosage': 'Dosage', 'arm_efficacy_metric': 'Metric',
                  'arm_efficacy_results': 'Efficacy Results'}
    df = df.rename(columns=rename_map, errors='raise')

    # Save Table
    df.to_excel(output_path, index=False)
    return df


if __name__ == '__main__':
    input_struct = '/data/rsg/nlp/juanmoo1/projects/02_takeda_dev/00_takeda/tmp/structs/test_docs_v2/struct_rd.json'
    output_table = '/data/rsg/nlp/juanmoo1/projects/02_takeda_dev/00_takeda/tmp/table/test_docs.xlsx'
    output_dir = '/data/rsg/nlp/juanmoo1/projects/02_takeda_dev/00_takeda/tmp/table/'

    create_table(input_struct, output_table, output_dir=output_dir)
