"""
Returns a specified assertion valueset.

Uses assertionvaluesets, a Pandas DataFrame of valueset information
obtqined by the SenLib class and cached in the current app.

"""
from typing import Any

from flask import Blueprint, jsonify, current_app, request
import pandas as pd

# Used to obtain the valueset for location, which is obtained from the hs-ontology-api
# instead of the senlib database.
from models.ontology_class import OntologyAPI
# application configuration
from models.appconfig import AppConfig
# Interface to MySql database
from models.senlib_mysql import SenLibMySql

import logging
# Configure consistent logging. This is done at the beginning of each module instead of with a superclass of
# logger to avoid the need to overload function calls to logger.
logging.basicConfig(format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
                    level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

valueset_blueprint = Blueprint('valueset', __name__, url_prefix='/valueset')


def build_valueset_cache() -> dict[str, Any]:
    cfg = AppConfig()
    database = SenLibMySql(cfg=cfg)
    df = database.assertionvaluesets

    # loop through the unique predicates in the db and build cache.
    cache = {}
    for predicate in df['predicate_term'].unique():
        if predicate == 'located_in':
            # Query the hs-ontology-api to get list of SenNet organs.
            ontapi = OntologyAPI()
            endpoint = 'organs?application_context=sennet'
            response = ontapi.get_ontology_api_response(endpoint=endpoint, target='organs')
            listret = [
                {'id': resp.get('organ_uberon'), 'label': resp.get('term')}
                for resp in response
            ]
        else:
            # Convert the valueset dataframe to desired list of dicts
            listret = [
                {'id': row['valueset_code'], 'label': row['valueset_term']}
                for _, row in getapp_assertionvalueset(predicate=predicate, df=df).iterrows()
            ]

        cache[predicate] = listret

    return cache


def getapp_assertionvalueset(predicate: str, df: pd.DataFrame) -> pd.DataFrame:
    """
    Obtain the valueset associated with an assertion predicate.
    :param predicate: assertion predicate. Can be either an IRI or a term.
    """

    # Check whether the predicate corresponds to an IRI.
    dfassertion = df[df['predicate_IRI'] == predicate]
    if len(dfassertion) == 0:
        # Check whether the predicate corresponds to a term.
        dfassertion = df[df['predicate_term'] == predicate]

    return dfassertion


@valueset_blueprint.route('', methods=['GET'])
def valueset():
    # Get the assertion predicate.
    predicate = request.args.get('predicate')

    # Obtain the valueset for the predicate from the cache.
    valueset_cache = current_app.valueset_cache
    result = valueset_cache.get(predicate)
    if result is None:
        return jsonify({'error': f'No valueset found for predicate {predicate}'}), 404

    return jsonify(result)
