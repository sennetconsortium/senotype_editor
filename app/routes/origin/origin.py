"""
Wraps calls to the SciCrunch Resolver API SciCruch detail pages to obtain
information on origins.
"""

from flask import Blueprint, jsonify, redirect

from models.appconfig import AppConfig
from models.requestretry import RequestRetry

origin_blueprint = Blueprint('origin', __name__, url_prefix='/origin')


@origin_blueprint.route('/search/<searchterm>', methods=['GET'])
def getoriginsearchterm(searchterm):

    """
    Search SciCrunch Resolver for origins that match the search term.
    :param searchterm: search term
    """
    cfg = AppConfig()
    base_url = cfg.getfield(key='SCICRUNCH_BASE_URL')

    url = f"{base_url}{searchterm}.json"
    api = RequestRetry()
    resp = api.getresponse(url=url, format='json')
    return jsonify(resp)


# Return the SciCrunch home page.
@origin_blueprint.route('/detail', methods=['GET'])
def getorigindetailroute():
    return getorigindetail()


# Return the SciCrunch detail page for an origin.
@origin_blueprint.route('/detail/<id>', methods=['GET'])
def getorigindetailidroute(id):
    return getorigindetail(id)


def getorigindetail(id: str = ''):

    """
    Redirects to the SciCrunch Resolver detail page for the specified RRID.
    :param id: RRID
    """
    cfg = AppConfig()
    base_url = cfg.getfield(key='SCICRUNCH_BASE_URL')
    url = f"{base_url}{id}"
    return redirect(url)


@origin_blueprint.route('/explore', methods=['GET'])
def getscicrunchexploresearch():
    cfg = AppConfig()
    url = cfg.getfield(key='SCICRUNCH_EXPLORE_URL')
    return redirect(url)


