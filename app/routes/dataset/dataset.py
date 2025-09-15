from flask import redirect, session, Blueprint, Response
import requests

dataset_blueprint = Blueprint('dataset', __name__, url_prefix='/dataset')


@dataset_blueprint.route('/portal/<entity_id>', methods=['GET'])
def get_dataset(entity_id):
    """
    Redirects the user to the Data Portal dataset page for the given SenNet ID.
    param entity_id: SenNet ID
    """
    token = session["groups_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get the uuid for this SenNet ID
    url_entity = f"https://entity.api.sennetconsortium.org/entities/{entity_id}"
    resp = requests.get(url=url_entity, headers=headers)
    if not resp.ok:
        # Optionally handle error (e.g. flash message, abort, etc.)
        return "SenNet ID not found", 404

    respjson = resp.json()
    uuid = respjson.get('uuid')
    if not uuid:
        return "UUID not found", 404

    # Redirect the browser to the Data Portal dataset page
    url_portal = f"https://data.sennetconsortium.org/dataset?uuid={uuid}"
    return redirect(url_portal)