"""
Returns a specified valueset.
"""

from flask import Blueprint, jsonify, current_app, make_response, request

# Helper classes
from models.appconfig import AppConfig
from models.senlib import SenLib

valueset_blueprint = Blueprint('valueset', __name__, url_prefix='/valueset')

@valueset_blueprint.route('', methods=['GET'])
def valueset():
    # Read the app.cfg file outside the Flask application context.
    cfg = AppConfig()

    # Get IDs for existing Senotype submissions.
    # Get the URLs to the senlib repo.
    senlib_url = cfg.getfield(key='SENOTYPE_URL')
    valueset_url = cfg.getfield(key='VALUESET_URL')
    json_url = cfg.getfield(key='JSON_URL')
    # Github personal access token for authorized calls
    github_token = cfg.getfield(key='GITHUB_TOKEN')

    # Senlib interface
    senlib = SenLib(senlib_url, valueset_url, json_url, github_token)

    # Get the assertion predicate.
    predicate = request.args.get('predicate')

    # Convert to desired list of dicts
    listret = [
        {'id': row['valueset_code'], 'label': row['valueset_term']}
        for _, row in senlib.getsenlibvalueset(predicate=predicate).iterrows()
    ]


    return jsonify(listret)