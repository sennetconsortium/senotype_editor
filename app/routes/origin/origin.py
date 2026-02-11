"""
Wraps calls to the SciCrunch Resolver API and SciCruch detail pages to obtain
information on origins.
"""

from flask import Blueprint, jsonify, redirect

from models.appconfig import AppConfig
from models.requestretry import RequestRetry

origin_blueprint = Blueprint('origin', __name__, url_prefix='/origin')

def translate_searchurl(searchterm:str)->str:
    """
    Uses the searchterm to create the appropriate search URL
    for SciCrunch Resolver.

    Origins in SciCrunch can have identifiers with higher resolution than
    the RRID.

    Antibodies and cell lines are offered by multiple vendors.
    The complete id for an antibody or cell line is in a dash-delimited format, with the vendor id
    at the end.

    :param searchterm: search term
    """

    cfg = AppConfig()
    if '-' in searchterm:
        print('high-level')
        # The dash is the delimiter used in higher-resolution IDs.

        base_url = cfg.getfield(key='SCICRUNCH_HIGHER_URL')
        # Move the vendor ID into a parameter of the higher-resolution URL.
        lower_param = searchterm.split('-')[0]
        searchterm = f'{lower_param}?i=rrid%3A{searchterm}'
    else:
        # This is a lower-resolution search term, for RRIDs.
        base_url = cfg.getfield(key='SCICRUNCH_BASE_URL')
        searchterm = f'{searchterm}'

    print('final searchterm: ', searchterm)
    return f'{base_url}{searchterm}'

@origin_blueprint.route('/search/<searchterm>', methods=['GET'])
def getoriginsearchterm(searchterm):

    """
    Search SciCrunch Resolver for origins that match the search term.
    :param searchterm: search term
    """

    # Determine the search URL, based on whether the identifier
    # is high-resolution (e.g., antibodies or cell lines, with resolution
    # at the vendor level) or low-resolution (at the RRID level).
    searchurl = translate_searchurl(searchterm)
    url = f"{searchurl}.json"
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

    searchurl = translate_searchurl(id)
    url = f"{searchurl}"
    return redirect(url)


@origin_blueprint.route('/explore', methods=['GET'])
def getscicrunchexploresearch():
    cfg = AppConfig()
    url = cfg.getfield(key='SCICRUNCH_EXPLORE_URL')
    return redirect(url)


