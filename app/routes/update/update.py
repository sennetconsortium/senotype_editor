"""
Updates the Senotype repository by writing/overwriting a submission JSON file.
"""
from flask import Blueprint, request, render_template, jsonify
import uuid

# Helper classes
from models.appconfig import AppConfig
from models.senlib import SenLib

update_blueprint = Blueprint('update', __name__, url_prefix='/update')


def getnewsnid() -> str:
    """
    Mint a new SenNet ID.
    The uuid-api does not currently support Senotype.
    For now, generate a generic uuid.
    """

    return str(uuid.uuid4())

def buildsubmission(form_data: dict[str, str]) -> dict:
    """
    Builds a Senotype submission JSON from the POSTed request form data.

    """

    senotypeid = request.form.get('senotypeid')
    if senotypeid == 'new':
        senotypeid = getnewsnid()

    dictsenotype = {
        'code': senotypeid,
        'term': request.form.get('senotypename'),
        'definition': request.form.get('senotypedescription')
    }
    dictsubmission = {
        'senotype': dictsenotype
    }

    return dictsubmission

@update_blueprint.route('', methods=['POST', 'GET'])
def update():

    # Read the app.cfg file outside the Flask application context.
    cfg = AppConfig()

    # Get IDs for existing Senotype submissions.
    # Get the URLs to the senlib repo.
    senlib_url = cfg.getfield(key='SENOTYPE_URL')
    valueset_url = cfg.getfield(key='VALUESET_URL')
    json_url = cfg.getfield(key='JSON_URL')

    # Senlib interface
    senlib = SenLib(senlib_url, valueset_url, json_url)

    dictsenotype = buildsubmission(form_data=request.form)
    return jsonify(dictsenotype)




