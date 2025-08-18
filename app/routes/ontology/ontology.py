"""
Calls the hs-ontology API.
"""
from flask import Blueprint
from models.requestretry import RequestRetry

ontology_blueprint = Blueprint('ontology', __name__, url_prefix='/ontology')


@ontology_blueprint.route('/genes/<subpath>')
def ontology_genes_proxy(subpath):
    api = RequestRetry()
    url = f'https://ontology.api.hubmapconsortium.org/genes/{subpath}'
    return api.getresponse(url=url, format='json')


@ontology_blueprint.route('/proteins/<subpath>')
def ontology_proteins_proxy(subpath):
    api = RequestRetry()
    url = f'https://ontology.api.hubmapconsortium.org/proteins/{subpath}'
    return api.getresponse(url=url, format='json')
