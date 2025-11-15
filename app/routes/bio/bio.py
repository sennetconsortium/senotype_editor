"""
Wraps calls to search and detail pages for ontologies related to:
cell types
genes
proteins
"""

from flask import Blueprint, jsonify, redirect, abort

from models.appconfig import AppConfig
from models.requestretry import RequestRetry

bio_blueprint = Blueprint('bio', __name__, url_prefix='/bio')


@bio_blueprint.route('/obo/detail', methods=['GET'])
def getobodetailroute():
    return getobodetail()


# Return the SciCrunch detail page for an origin.
@bio_blueprint.route('/obo/detail/<id>', methods=['GET'])
def getobodetailidroute(id):
    return getobodetail(id)


def getobodetail(id: str = ''):

    """
    Redirects to the OBO detail page for the specified id.
    :param id: id
    """
    cfg = AppConfig()
    base_url = cfg.getfield(key='OBO_BASE_URL')
    url = f"{base_url}{id}"
    return redirect(url)


# Load the home page for the relevant ontology.
@bio_blueprint.route('/home/<id>', methods=['GET'])
def getbiohome(id: str):
    cfg = AppConfig()

    if id.upper() == 'CL':
        url = cfg.getfield(key='CL_HOME_URL')
    elif id.upper() == 'DOID':
        url = cfg.getfield(key='DOID_HOME_URL')
    else:
        abort(404, f"unknown home id {id}")

    return redirect(url)


