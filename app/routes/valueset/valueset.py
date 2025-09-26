"""
Returns a specified assertion valueset.

Uses assertionvaluesets, a Pandas DataFrame of valueset information
obtqined by the SenLib class and cached in the current app.

"""

from flask import Blueprint, jsonify, current_app, request
import pandas as pd

valueset_blueprint = Blueprint('valueset', __name__, url_prefix='/valueset')


def getapp_assertionvalueset(predicate: str) -> pd.DataFrame:
    """
    Obtain the valueset associated with an assertion predicate.
    :param dfvaluesets: valueset dataframe
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

    # Convert to desired list of dicts
    listret = [
        {'id': row['valueset_code'], 'label': row['valueset_term']}
        for _, row in getapp_assertionvalueset(predicate=predicate).iterrows()
    ]

    return jsonify(listret)