"""
add_terms.py

One-off script to populate retroactively terms into the senotype JSONs.
Initially, senotypes only contained codes, and terms were fetched for display in the
UI when the senotype was selected.

"""
import os
import configobj
import argparse
from tqdm import tqdm
import pandas as pd

from models.appconfig import AppConfig
from models.senlib_mysql import SenLibMySql
from models.requestretry import RequestRetry

class RawTextArgumentDefaultsHelpFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawTextHelpFormatter
):
    pass

def getargs() -> argparse.Namespace:
    """
    Obtains command line arguments.
    :return: parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description='Add terms to the senotype JSONs.',
        formatter_class=RawTextArgumentDefaultsHelpFormatter)

    parser.add_argument("-g", '--group', type=str,
                        help='SenNet group token', required=True)

    parser.add_argument("-i", '--id', type=str,
                        help='Senotype ID', required=False)
    args = parser.parse_args()

    return args

def getcitationtitle(pmid: str) -> str:
    """
    Calls the NCBI EUtils API to obtain the title for the PMID.

    """
    # print('Getting citation data from NCBI EUtils')
    cfg = AppConfig()
    base_url = cfg.getfield(key='EUTILS_SUMMARY_BASE_URL')

    # The NCBI API Key allows for more than 3 searches/second. Without the API Key,
    # calls to EUtils will be erratic because of 429 errors.
    api_key = cfg.getfield(key='EUTILS_API_KEY')
    id = pmid.split('PMID:')[1]
    url = f"{base_url}&id={id}&api_key={api_key}"

    api = RequestRetry()
    citation = api.getresponse(url=url, format='json')
    result = citation.get('result')
    title = 'unknown'
    if result is not None:
        entry = result.get(id)
        if entry is not None:
            title = entry.get('title', '')
    return title

def getorigindescription(code: str) -> str:
    """
    Calls the SciCrunch API to obtain the title for a RRID.
    :param: code - the RRID code
    """

    # print('Getting origin information from SciCrunch Resolver')
    cfg = AppConfig()
    api = RequestRetry()

    base_url = cfg.getfield(key='SCICRUNCH_BASE_URL')

    # IDs for Antibodies and cells have higher resolution (vendor)
    # than RRID, using the dash as delimiter. However, the
    # search URL that returns JSON only has resolution at the
    # RRID level. Strip higher-resolution identifiers.
    searchcode = code
    if '-' in code:
        searchcode = code.split('-')[0]
    url = f'{base_url}{searchcode}.json'

    origin = api.getresponse(url=url, format='json')
    description = 'unknown'
    if origin is not None:
        hits = origin.get('hits')
        if hits is not None:
            if len(hits.get('hits')) > 0:
                description = hits.get('hits')[0].get('_source').get('item').get('name', '')

    return description

def getdatasettitle(snid:str, group:str) -> str:

        """
        Calls the entity API to obtain the title for a SenNet dataset.
        :param snid: SenNet dataset identifier.
        :param group: A SenNet group token
        """

        # print('Getting dataset information from SenNet entity-api')
        cfg = AppConfig()
        api = RequestRetry()

        headers = {"Authorization": f'Bearer {group}'}
        base_url = cfg.getfield(key='ENTITY_BASE_URL')
        url = f'{base_url}{snid}'
        dataset = api.getresponse(url=url, format='json', headers=headers)
        title = dataset.get('title', '')
        if title is None or title.strip() == '':
            title = 'unknown'

        return title

def getcelltypeterm(code: str) -> str:
    """
    Calls the UBKG API to obtain descriptions for cell types.
    :param code: cell type code
    """

    # print('Getting celltype information from the ontology API')
    cfg = AppConfig()
    api = RequestRetry()

    base_url = f"{cfg.getfield(key='UBKG_BASE_URL')}/celltypes/"
    url = f'{base_url}{code.split("CL:")[1]}'
    celltype = api.getresponse(url=url, format='json')

    name = 'unknown'
    # celltypes returns a list of JSON objects
    if len(celltype) > 0:
        name = celltype[0].get('cell_type').get('name', '')

    return name

def getlocationterm(code: str) -> str:
    """
    Calls the UBKG API to obtain descriptions for an organ.
    :param code: organ code
    """

    # print('Getting organ information from the ontology API')
    cfg = AppConfig()
    api = RequestRetry()

    url = f"{cfg.getfield(key='UBKG_BASE_URL')}/organs?application_context=sennet"

    organs = api.getresponse(url=url, format='json')

    # organs returns a list of JSON objects
    term = 'unknown'
    if len(organs) > 0:
        for o in organs:
            if o['organ_uberon'] == code:
                term = o['term']

    return term

def getdiagnosisterm(code: str) -> str:
    """
    Calls the UBKG API to obtain descriptions for diagnoses.
    :param code: diagnose code
    """
    # print('Getting diagnosis information from the ontology API')
    api = RequestRetry()
    cfg = AppConfig()

    url = f"{cfg.getfield(key='UBKG_BASE_URL')}/codes/{code}/terms"

    diagnoses = api.getresponse(url=url, format='json')

    # diagnoses returns a list of JSON objects
    term = 'unknown'
    if len(diagnoses) > 0:
        for d in diagnoses:
            for t in d['terms']:
                if t['term_type'] == 'PT':
                    term = t['term']

    return term

def getmarkerdescription(code: str) -> str:
    """
    Calls the UBKG API to obtain the description for specified markers.
    :param: code - marker code
    """

    # print('Getting marker information from the ontology API')
    cfg = AppConfig()
    api = RequestRetry()

    base_url = cfg.getfield('UBKG_BASE_URL')

    markerid = code.split(':')[1]
    markertype = code.split(':')[0]
    if markertype == 'HGNC':
        marker = 'genes'
    else:
        marker = 'proteins'

    url = f'{base_url}/{marker}/{markerid}'

    resp = api.getresponse(url=url, format='json')
    # Defensive: check if resp is a list and not empty
    term = 'unknown'

    if not resp or not isinstance(resp, list) or not resp[0]:
        term = 'unknown'
    else:
        data = resp[0]
        if 'HGNC' in code:
            # For genes
            term = data.get('approved_symbol', code)
        else:
            # For proteins
            recommended_names = data.get('recommended_name')
            if isinstance(recommended_names, list) and recommended_names:
                term = recommended_names[0].strip()
            else:
                term = code
    return term

def getvaluesetterm(code: str, pred:str, vs: dict) -> str:
    """
    Obtains the term for a member of a value set.
    :param code: value set code
    :param pred: The predicate to get the term for
    :param valuesets: valueset information
    """

    term = ''
    vs_pred = vs[vs['predicate_term']==pred]
    if len(vs_pred)>0:
        term = vs_pred.loc[vs_pred['valueset_code']==code]['valueset_term'].values[0]
    return term

def gettermforcode(code: str, pred: str, group: str, vs: dict) -> str:
    """
    Obtains the term for the given code, based on the predicate.
    :param code: The code to get the term for
    :param pred: The predicate to get the term for
    :param group: A SenNet group token

    """
    api = RequestRetry()
    cfg = AppConfig()

    term = ''
    if pred == 'has_citation':
        term = getcitationtitle(pmid=code)
    elif pred == 'has_origin':
        term = getorigindescription(code=code)
    elif pred == 'has_dataset':
        term = getdatasettitle(snid=code, group=group)
    elif pred == 'has_cell_type':
        term = getcelltypeterm(code=code)
    elif pred == 'located_in':
        term = getlocationterm(code=code)
    elif pred == 'has_diagnosis':
        term = getdiagnosisterm(code=code)
    elif pred in ['has_characterizing_marker_set','up_regulates', 'down_regulates', 'inconclusively_regulates']:
        term = getmarkerdescription(code=code)
    else:
        # valueset
        term = getvaluesetterm(code=code, pred=pred, vs=vs)

    return term

def main():

    # Obtaining SenNet dataset titles requires a SenNet groups token.
    args = getargs()

    # Get configuration information.
    cfg = AppConfig()

    # Connect to the Senotype database.
    senlib = SenLibMySql(cfg=cfg)

    # Loop through senotypes.
    senotypejsons = senlib.getallsenotypejsons()
    updated_senotypejsons = []

    for senotypejson in senotypejsons:

        # Copy the existing senotype JSON.
        id = senotypejson["senotype"]["id"]
        print(id)

        # Allow update for a specific senotype.
        if id == args.id or args.id is None:
            updated_senotypejson= {
                "senotype": senotypejson['senotype'],
                "submitter": senotypejson['submitter']}

            # Loop through the senotype's set of assertions.
            assertions = senotypejson.get('assertions')
            updated_assertions = []

            for assertion in assertions:
                updated_assertion = { "predicate": assertion['predicate']}

                pred = assertion['predicate']['term']
                print('assertion: ',pred)

                # Loop through the assertion's objects.
                objects = assertion.get('objects')
                updated_objects = []

                for object in tqdm(objects):
                    if pred == 'has_context':
                        # Copy context assertions without translation.
                        updated_object = object
                    else:
                        # Add term key to object.
                        code = object['code']
                        source = object['source']
                        vs = senlib.assertionvaluesets
                        term = gettermforcode(code=code, pred=pred, vs=vs, group=args.group)
                        updated_object = {"code": code,
                                          "source": source,
                                          "term": term}
                    updated_objects.append(updated_object)

                updated_assertion['objects'] = updated_objects
                updated_assertions.append(updated_assertion)

            updated_senotypejson['assertions'] = updated_assertions
            updated_senotypejsons.append(updated_senotypejson)

    # Update the senotypes in the database.
    for j in updated_senotypejsons:
        print(f'UPDATING {id}')
        id = j["senotype"]["id"]
        senlib.writesenotype(senotypeid=id, senotypejson=j)

if __name__ == "__main__":
    main()