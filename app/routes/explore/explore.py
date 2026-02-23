"""
Wraps calls to detail pages for:
HGNC
UNIPROTKB

Used by the modal windows that add individual specified markers or
regulating markers.
"""

from flask import Blueprint, redirect, abort

from models.appconfig import AppConfig

explore_blueprint = Blueprint('explore', __name__, url_prefix='/explore')

# Return the specified home page.
@explore_blueprint.route('/<id>', methods=['GET'])
def getmarkerdetailidroute(id):
    cfg = AppConfig()

    if 'HGNC' in id.upper():
        base_url = cfg.getfield(key='HGNC_HOME_URL')
    elif 'UNIPROTKB' in id.upper():
        base_url = cfg.getfield(key='UNIPROTKB_BASE_URL')
    else:
        abort(404, f"unknown sab {id}")

    url = f"{base_url}"
    return redirect(url)





