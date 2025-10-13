"""
Calls the hs-ontology API.

"""
from flask import Blueprint, make_response
from models.requestretry import RequestRetry
from models.appconfig import AppConfig

ontology_blueprint = Blueprint('ontology', __name__, url_prefix='/ontology')


@ontology_blueprint.route('/genes/<subpath>')
def ontology_genes_proxy(subpath):
    api = RequestRetry()
    cfg = AppConfig()
    url = f"{cfg.getfield(key='UBKG_BASE_URL')}/genes/{subpath}"
    response = api.getresponse(url=url, format='json')
    if type(response) is dict:
        return make_response('no genes found', 400)
    else:
        return response


@ontology_blueprint.route('/proteins/<subpath>')
def ontology_proteins_proxy(subpath):
    api = RequestRetry()
    cfg = AppConfig()
    url = f"{cfg.getfield(key='UBKG_BASE_URL')}/proteins/{subpath}"
    response = api.getresponse(url=url, format='json')
    if type(response) is dict:
        return make_response('no proteins found', 400)
    else:
        return response
