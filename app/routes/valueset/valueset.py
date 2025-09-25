"""
Returns a specified valueset.
"""

from flask import Blueprint, jsonify, current_app, make_response, request, session

# Helper classes
from models.appconfig import AppConfig
from models.senlib import SenLib

valueset_blueprint = Blueprint('valueset', __name__, url_prefix='/valueset')


@valueset_blueprint.route('', methods=['GET'])
def valueset():
    # Read the app.cfg file outside the Flask application context.
    cfg = AppConfig()
    # Senlib interface
    senlib = SenLib(cfg, userid=session['userid'])

    # Get the assertion predicate.
    predicate = request.args.get('predicate')

    # Convert to desired list of dicts
    listret = [
        {'id': row['valueset_code'], 'label': row['valueset_term']}
        for _, row in senlib.getassertionvalueset(predicate=predicate).iterrows()
    ]

    return jsonify(listret)