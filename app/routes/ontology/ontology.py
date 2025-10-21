"""
Calls the hs-ontology API.

"""
from flask import Blueprint
from models.ontology_class import OntologyAPI

ontology_blueprint = Blueprint('ontology', __name__, url_prefix='/ontology')
ontapi = OntologyAPI()

@ontology_blueprint.route('/genes/<subpath>')
def ontology_genes_proxy(subpath):

    endpoint = f'genes/{subpath}'
    return ontapi.get_ontology_api_response(endpoint=endpoint,target='genes')


@ontology_blueprint.route('/proteins/<subpath>')
def ontology_proteins_proxy(subpath):

    endpoint = f'proteins/{subpath}'
    return ontapi.get_ontology_api_response(endpoint=endpoint, target='proteins')


@ontology_blueprint.route('/celltypes/<subpath>')
def ontology_celltypes_proxy(subpath):

    endpoint = f'celltypes/{subpath}'
    return ontapi.get_ontology_api_response(endpoint=endpoint, target='celltypes')


@ontology_blueprint.route('/diagnoses/<subpath>/term')
def ontology_diagnoses_proxy_term(subpath):

    # Returns information on a diagnosis based on a search string.

    # First get the DOID code corresponding to the search term.
    endpoint = f'terms/{subpath}/codes'
    response = ontapi.get_ontology_api_response(endpoint=endpoint, target='diagnoses')
    # The response is either a list of dicts or a dict with a message key.
    doi_response = []
    if type(response) is list:
        for r in response:
            sab = r.get('code').split(':')[0]
            code = r.get('code')
            if sab in ['DOID']:
                # Get the PT for the diagnosis code.
                endpoint2 = f"codes/{code}/terms"
                response2 = ontapi.get_ontology_api_response(endpoint=endpoint2, target='diagnoses')
                terms = response2.get('terms')
                for t in terms:
                    if t.get('term_type') == 'PT':
                        doi_response.append({'code': code, 'term': t.get('term')})
    return doi_response

@ontology_blueprint.route('/diagnoses/<subpath>/code')
def ontology_diagnoses_proxy_code(subpath):
    # Returns information on a diagnosis based on a code.

    endpoint = f'codes/{subpath}/terms'
    response = ontapi.get_ontology_api_response(endpoint=endpoint, target='diagnoses')

    doi_response = []
    terms = response.get('terms')
    for t in terms:
        if t.get('term_type') == 'PT':
            doi_response.append({'code': subpath, 'term': t.get('term')})

    return doi_response

