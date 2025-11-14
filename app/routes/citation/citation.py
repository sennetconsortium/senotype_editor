"""
Wraps calls to the NCBI PubMed EUtils API and NCBI PubMed detail pages to obtain
information on citations.
"""

from flask import Blueprint, jsonify, redirect

from models.appconfig import AppConfig
from models.requestretry import RequestRetry

citation_blueprint = Blueprint('citation', __name__, url_prefix='/citation')


@citation_blueprint.route('/search/term/<searchterm>', methods=['GET'])
def getcitationsearchterm(searchterm):

    """
    Search NCBI EUtils for publications that match the search term.
    :param searchterm: search term
    """
    cfg = AppConfig()
    base_url = cfg.getfield(key='EUTILS_SEARCH_BASE_URL')
    # The NCBI API Key allows for more than 3 searches/second. Without the API Key,
    # calls to EUtils will be erratic because of 429 errors.
    api_key = cfg.getfield(key='EUTILS_API_KEY')

    url = f"{base_url}&term={searchterm}&api_key={api_key}"
    api = RequestRetry()
    resp = api.getresponse(url=url, format='json')
    return jsonify(resp)


@citation_blueprint.route('/search/id/<ids>', methods=['GET'])
def getcitationsearchid(ids):

    """
    Search NCBI EUtils for information on the set of publications identified in the list of ids.
    :param ids: comma-delimited set of PMIDs.
    """
    cfg = AppConfig()
    base_url = cfg.getfield(key='EUTILS_SUMMARY_BASE_URL')

    # The NCBI API Key allows for more than 3 searches/second. Without the API Key,
    # calls to EUtils will be erratic because of 429 errors.
    api_key = cfg.getfield(key='EUTILS_API_KEY')
    url = f"{base_url}&id={ids}&api_key={api_key}"

    api = RequestRetry()
    resp = api.getresponse(url=url, format='json')
    return jsonify(resp)


# Return the PubMed home page.
@citation_blueprint.route('/detail', methods=['GET'])
def getcitationdetailroute():
    return getcitationdetail()


# Return the PubMed detail page for a publication.
@citation_blueprint.route('/detail/<id>', methods=['GET'])
def getcitationdetailidroute(id: str = ''):
    return getcitationdetail(id)


def getcitationdetail(id):

    """
    Redirects to the PubMed detail page for the specified PMID.
    :param id: PMID
    """
    cfg = AppConfig()
    base_url = cfg.getfield(key='PUBMED_BASE_URL')
    url = f"{base_url}{id}"
    return redirect(url)
