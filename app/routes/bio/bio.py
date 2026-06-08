"""
Wraps calls to search and detail pages for ontologies related to:
cell types
genes
proteins
"""

from flask import Blueprint, redirect, abort, request

from models.appconfig import AppConfig
from models.ontology_class import OntologyAPI
from utils.http_param import HttpParam

bio_blueprint = Blueprint('bio', __name__, url_prefix='/bio')
ontapi = OntologyAPI()
http_param = HttpParam()

@bio_blueprint.route('/obo/detail', methods=['GET'])
def getobodetailroute():
    return getbiodetail(sab='OBO')


# Return the detail page for the biological entity.
@bio_blueprint.route('/obo/detail/<id>', methods=['GET'])
def getobodetailidroute(id):
    return getbiodetail(sab='OBO', id=id)


@bio_blueprint.route('/marker/detail/<id>', methods=['GET'])
def getmarkerdetailidroute(id):
    if 'HGNC' in id.upper():
        return gethgncdetailidroute(id)
    elif 'MGI' in id.upper():
        return getmgidetailidroute(id)
    else:
        return getuniprotkbdetailidroute(id)


@bio_blueprint.route('/hgnc/detail', methods=['GET'])
def gethgncdetailroute():
    return getbiodetail(sab='HGNC')


# Return the HGNC detail page for a human gene.
@bio_blueprint.route('/hgnc/detail/<id>', methods=['GET'])
def gethgncdetailidroute(id):
    return getbiodetail(sab='HGNC', id=id)

# Return the MGI detail page for a mouse gene.
@bio_blueprint.route('/mgi/detail/<id>', methods=['GET'])
def getmgidetailidroute(id):
    return getbiodetail(sab='MGI', id=id)


@bio_blueprint.route('/uniprotkb/detail', methods=['GET'])
def getuniprotkbdetailroute():
    return getbiodetail(sab='UNIPROTKB')


# Return the SciCrunch detail page for an origin.
@bio_blueprint.route('/uniprotkb/detail/<id>', methods=['GET'])
def getuniprotkbdetailidroute(id):
    return getbiodetail(sab='UNIPROTKB', id=id)


def _getmgisymbol(id: str):
    """
    Obtains the MGI approved symbol from a MGI ID, using the genes endpoint.
    """
    endpoint = f'genes/{id}?organism=mouse'
    ret = ontapi.get_ontology_api_response(endpoint=endpoint, target='genes')
    symbol = ''
    if len(ret) > 0:
        symbol = ret[0]['approved_symbol']
    return symbol

def getbiodetail(sab: str, id: str = ''):

    """
    Redirects to an ontology detail page for the specified id.
    :param sab: either OBO (for entities with PURL IRIs) or the UBKG SAB of the source
                ontology (e.g., HGNC, UNIPROTKB)
    :param id: id
    """
    cfg = AppConfig()
    idsubmit = id

    if sab.upper() == 'OBO':
        base_url = cfg.getfield(key='OBO_BASE_URL')
    elif sab.upper() == 'HGNC':
        if id == '':
            # Home page
            base_url = cfg.getfield(key='HGNC_HOME_URL')
        else:
            # Detail page
            base_url = cfg.getfield(key='HGNC_BASE_URL')
    elif sab.upper() == 'UNIPROTKB':
        # Strip the SAB from the code.
        base_url = cfg.getfield(key='UNIPROTKB_BASE_URL')
        idsubmit = id.split(':')[1]
    elif sab.upper() == 'MGI':
        base_url = cfg.getfield(key='MGI_BASE_URL')
        mgi_id = id.split(':')[1]
        # Get MGI symbol from MGI ID.
        idsubmit = _getmgisymbol(mgi_id)
    else:
        abort(404, f"unknown sab {sab}")

    url = f"{base_url}{idsubmit}"
    print(url)
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
        abort(404, f"unknown home page id {id}")

    return redirect(url)


