"""
Returns a specified assertion valueset.

Uses assertionvaluesets, a Pandas DataFrame of valueset information
obtqined by the SenLib class and cached in the current app.

"""

from flask import Blueprint, jsonify, current_app, request
import pandas as pd

# Used to obtain the valueset for location, which is obtained from the hs-ontology-api
# instead of the senlib database.

from models.ontology_class import OntologyAPI


valueset_blueprint = Blueprint('valueset', __name__, url_prefix='/valueset')


def getapp_assertionvalueset(predicate: str) -> pd.DataFrame:
    """
    Obtain the valueset associated with an assertion predicate.
    :param predicate: assertion predicate. Can be either an IRI or a term.
    """

    df = current_app.assertionvaluesets
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

    if predicate == 'located_in':
        # Query the hs-ontology-api to get list of SenNet organs.
        ontapi = OntologyAPI()
        endpoint = f'organs?application_context=sennet'
        response = ontapi.get_ontology_api_response(endpoint=endpoint, target='organs')
        listret = [
            {'id': resp.get('organ_uberon'), 'label': resp.get('term')}
            for resp in response
        ]
    else:
        # Convert the valueset dataframe to desired list of dicts
        listret = [
            {'id': row['valueset_code'], 'label': row['valueset_term']}
            for _, row in getapp_assertionvalueset(predicate=predicate).iterrows()
        ]

    return jsonify(listret)
