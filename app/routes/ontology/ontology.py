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