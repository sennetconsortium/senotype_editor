"""
The dataset routes allow the Edit page to call the entity-api and SenNet Data Portal page
and pass a request body that includes the Globus authentication token.

"""
from flask import redirect, session, Blueprint, url_for, jsonify
import requests
from models.appconfig import AppConfig


dataset_blueprint = Blueprint('dataset', __name__, url_prefix='/dataset')


@dataset_blueprint.route('/<entity_id>', methods=['GET'])
def get_dataset_api(entity_id):
    """
    Obtains dataset from the entity-api.
    :param entity_id: SenNet ID (SNnnn.XXXX.nnn)

    """

    # If the user has not been authenticated by Globus, redirect
    # to the Globus login route.
    if 'groups_token' not in session:
        return redirect(url_for('globus.globus'))

    # Obtain Globus authentication token.
    token = session["groups_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get the uuid for this SenNet ID.
    cfg = AppConfig()
    base_url = cfg.getfield(key='ENTITY_BASE_URL')
    url_entity = f"{base_url}{entity_id}"
    resp = requests.get(url=url_entity, headers=headers)
    if not resp.ok:
        # Optionally handle error (e.g. flash message, abort, etc.)
        return jsonify("SenNet ID not found"), 404
    respjson = resp.json()
    entity_type = respjson.get('entity_type')
    if entity_type != 'Dataset':
        msg = f"'{entity_id}' is a SenNet ID for a {entity_type}, not a Dataset."
        return jsonify(msg), 400

    return respjson


@dataset_blueprint.route('/portal/<entity_id>', methods=['GET'])
def get_dataset_portal_id(entity_id):
    """
    Redirects the user to the Data Portal dataset page for the given SenNet ID.
    param entity_id: SenNet ID (SNnnn.XXXX.nnn)
    """

    # First, call the API to get the uuid for the entity.
    respjson = get_dataset_api(entity_id=entity_id)

    if respjson is not None:
        uuid = respjson.get('uuid')
    if not uuid:
        return "UUID not found", 404

    # Redirect the browser to the Data Portal dataset page
    cfg = AppConfig()
    base_url = cfg.getfield(key='DATA_PORTAL_BASE_URL')
    url_portal = f"{base_url}/dataset?uuid={uuid}"
    return redirect(url_portal)


@dataset_blueprint.route('/portal/explore', methods=['GET'])
def get_dataset_portal_explore():
    """
    Redirect to the SenNet Data Portal page.
    """
    cfg = AppConfig()
    url = cfg.getfield(key='DATA_PORTAL_BASE_URL')
    return redirect(url)