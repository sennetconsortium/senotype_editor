"""
Wraps calls to the NCBI EUtils API.
"""

from flask import Blueprint, jsonify

from models.appconfig import AppConfig
from models.requestretry import RequestRetry

citation_blueprint = Blueprint('citation', __name__, url_prefix='/citation')


@citation_blueprint.route('/search/term/<searchterm>', methods=['GET'])
def getcitationsearchterm(searchterm):

    print('getcitationsearchterm')
    cfg = AppConfig()
    base_url = cfg.getfield(key='EUTILS_BASE_URL')
    api_key = cfg.getfield(key='EUTILS_API_KEY')
    url = f"{base_url}&term={searchterm}&api_key={api_key}"

    api = RequestRetry()
    resp = api.getresponse(url=url, format='json')
    return jsonify(resp)


@citation_blueprint.route('/search/id/<ids>', methods=['GET'])
def getcitationsearchid(ids):

    print('getcitationsearchid')
    cfg = AppConfig()
    base_url = cfg.getfield(key='EUTILS_BASE_URL')
    api_key = cfg.getfield(key='EUTILS_API_KEY')
    url = f"{base_url}&id={ids}&api_key={api_key}"

    api = RequestRetry()
    resp = api.getresponse(url=url, format='json')
    return jsonify(resp)
