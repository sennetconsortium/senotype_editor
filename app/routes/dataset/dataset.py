"""
The dataset routes allow the Edit page to call the entity-api and SenNet Data Portal page
and pass a request body that includes the Globus authentication token.

"""
from flask import redirect, session, Blueprint
import requests

dataset_blueprint = Blueprint('dataset', __name__, url_prefix='/dataset')


@dataset_blueprint.route('/<entity_id>', methods=['GET'])
def get_dataset_api(entity_id):
    """
    Obtains dataset from the entity-api.

    """
    token = session["groups_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get the uuid for this SenNet ID
    url_entity = f"https://entity.api.sennetconsortium.org/entities/{entity_id}"
    resp = requests.get(url=url_entity, headers=headers)
    if not resp.ok:
        # Optionally handle error (e.g. flash message, abort, etc.)
        return "SenNet ID not found", 404

    return resp.json()


@dataset_blueprint.route('/portal/<entity_id>', methods=['GET'])
def get_dataset_portal(entity_id):
    """
    Redirects the user to the Data Portal dataset page for the given SenNet ID.
    param entity_id: SenNet ID
    """

    # First, call the API to get the uuid for the entity.
    respjson = get_dataset_api(entity_id=entity_id)

    if respjson is not None:
        uuid = respjson.get('uuid')
    if not uuid:
        return "UUID not found", 404

    # Redirect the browser to the Data Portal dataset page
    url_portal = f"https://data.sennetconsortium.org/dataset?uuid={uuid}"
    return redirect(url_portal)
