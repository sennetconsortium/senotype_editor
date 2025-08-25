"""
Updates the Senotype repository by writing/overwriting a submission JSON file.
"""
from flask import Blueprint, request, render_template, flash, redirect, get_flashed_messages, session
import uuid

# Helper classes
from models.appconfig import AppConfig
from models.senlib import SenLib
from models.editform import EditForm

from models.clearerrors import clearerrors

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


def writesubmission():

    # Read the app.cfg file outside the Flask application context.
    cfg = AppConfig()

    # Get IDs for existing Senotype submissions.
    # Get the URLs to the senlib repo.
    senlib_url = cfg.getfield(key='SENOTYPE_URL')
    valueset_url = cfg.getfield(key='VALUESET_URL')
    json_url = cfg.getfield(key='JSON_URL')

    # Senlib interface
    senlib = SenLib(senlib_url, valueset_url, json_url)


@update_blueprint.route('', methods=['POST', 'GET'])
def update():
    """
    Receives POST from the update_form, which has all edit_form fields as hidden inputs (cloned by JS).
    Validates using WTForms and acts on result.
    """

    # Get IDs for existing Senotype submissions and URLs
    cfg = AppConfig()
    senlib_url = cfg.getfield(key='SENOTYPE_URL')
    valueset_url = cfg.getfield(key='VALUESET_URL')
    json_url = cfg.getfield(key='JSON_URL')
    senlib = SenLib(senlib_url, valueset_url, json_url)
    choices = [("new", "(new)")] + [(id, id) for id in senlib.senlibjsonids]

    form = EditForm(request.form)  # Use POSTed form data
    form.senotypeid.choices = choices  # Must reset choices for select field

    # Set selected value for senotypeid (to preserve selection)
    prior_senotypeid = request.form.get('senotypeid', 'new')
    form.senotypeid.data = prior_senotypeid

    # Clear messages.
    if 'flashes' in session:
        session['flashes'].clear()
    clearerrors(form)

    if form.validate():
        # Handle successful update (save to database, etc.)
        dictsenotype = buildsubmission(form_data=request.form)
        writesubmission()
        flash('Success!')
        return redirect('/edit')
    else:
        # Show errors on the editor page, re-render with flashed errors and prior values
        flash("Validation failed. Please check your inputs.", "danger")
        return render_template('edit.html', form=form, errors=form.errors)
