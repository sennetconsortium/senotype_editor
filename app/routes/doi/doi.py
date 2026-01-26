"""
Wraps calls to the DataCite API and DataCite Commons for information on
Digital Object Identifiers (DOIs).
"""

from flask import Blueprint, jsonify, redirect

from models.appconfig import AppConfig
from models.requestretry import RequestRetry

doi_blueprint = Blueprint('doi', __name__, url_prefix='/doi')


@doi_blueprint.route('/search/<id>', methods=['GET'])
def doi_search(id):
    """
    Call the DataCite API to obtain information on the specified doi.
    :param id: DOI ID

    """
    cfg = AppConfig()
    api_base_url = cfg.getfield(key='DATACITE_API_BASE_URL')
    # Limit the search to at least SenNet provided-ids.
    provider_id = cfg.getfield(key='DATACITE_SENOTYPE_PROVIDER_ID')

    # First: try to find the exact match
    url = f"{api_base_url}{provider_id}/{id}"
    api = RequestRetry()
    resp = api.getresponse(url=url, format='json')

    # The DataCite API does not include the DataCite prefix in its response, so
    # add it to the response.
    prefix = f"{cfg.getfield(key='DATACITE_DOI_BASE_URL')}{provider_id}/"
    resp['data']['prefix'] = prefix

    return jsonify(resp)


@doi_blueprint.route('/explore', methods=['GET'])
def getdoidetail_route():
    return getdoidetail()


@doi_blueprint.route('/detail/<id>', methods=['GET'])
def getdoidetail_id_route(id):
    return getdoidetail(id)


def getdoidetail(id: str = ''):

    # Return the detail page of a DOI in DataCite.
    cfg = AppConfig()
    base_url = cfg.getfield(key='DATACITE_HOME_URL')
    if id != '':
        # Add the DataCite provider ID for senotypes to the URL.
        provider_id = cfg.getfield(key='DATACITE_SENOTYPE_PROVIDER_ID')
        url = f"{base_url}/doi.org/{provider_id}/{id}"
    else:
        url = f"{base_url}{id}"

    return redirect(url)