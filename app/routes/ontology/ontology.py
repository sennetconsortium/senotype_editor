"""
Calls the hs-ontology API.

"""
from flask import Blueprint, make_response
from models.requestretry import RequestRetry

ontology_blueprint = Blueprint('ontology', __name__, url_prefix='/ontology')


@ontology_blueprint.route('/genes/<subpath>')
def ontology_genes_proxy(subpath):
    api = RequestRetry()
    url = f'https://ontology.api.hubmapconsortium.org/genes/{subpath}'
    response = api.getresponse(url=url, format='json')
    if type(response) is dict:
        return make_response('no genes found', 400)
    else:
        return response


@ontology_blueprint.route('/proteins/<subpath>')
def ontology_proteins_proxy(subpath):
    api = RequestRetry()
    url = f'https://ontology.api.hubmapconsortium.org/proteins/{subpath}'
    response = api.getresponse(url=url, format='json')
    if type(response) is dict:
        return make_response('no proteins found', 400)
    else:
        return response
