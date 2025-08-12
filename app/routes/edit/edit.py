"""
Senotype edit route.
Works with editform.py.

"""

from flask import Blueprint, request, render_template, flash, session, abort
from wtforms import SelectField, Field

# WTForms
from models.editform import EditForm

# Helper classes
# Represents the app.cfg file
from models.appconfig import AppConfig
from models.senlib import SenLib

edit_blueprint = Blueprint('edit', __name__, url_prefix='/edit')

def getassertiondata(assertions: list, predicate: str) -> str:
    """
    Obtains information for the specified assertion from the Senotype submission
    JSON.
    :param assertions: list of assertion objects
    :param predicate: corresponds to predicate key
    """

    for assertion in assertions:
        assertion_predicate = assertion.get('predicate')



@edit_blueprint.route('', methods=['POST', 'GET'])
def edit():

    # Read the app.cfg file outside the Flask application context.
    cfg = AppConfig()

    # Get IDs for existing Senotype submissions.
    # Get the URL to the senlib repo.
    github_url = cfg.getfield(key='GITHUB_URL')
    senlib = SenLib(url=github_url)
    # Add 'new' as an option. Must be a tuple for correct display in the form.
    choices = [("new", "(new)")] + [(id, id) for id in senlib.senlibjsonids]

    # Load the edit form and the edit page.
    form = EditForm(request.form)
    form.senotypeid.choices = choices

    if request.method == 'GET':
        # This is from the redirect from the login page.
        # Set defaults.
        form.senotypename.data = ''
        form.senotypedescription.data = ''
        form.submitterfirst.data = ''
        form.submitterlast.data = ''
        form.submitteremail.data = ''

    if request.method == 'POST' and form.validate():
        # This is a result of the user selecting something other than 'new'
        # for a Senotype ID--i.e, an existing senotype. Load data.

        id = form.senotypeid.data

        # Get senotype data
        dictsenlib = senlib.getsenlibjson(id=id)

        senotype = dictsenlib.get('senotype')
        form.senotypename.data = senotype.get('term', '')
        form.senotypedescription.data = senotype.get('definition')

        # Submitter data
        submitter = dictsenlib.get('submitter')
        submitter_name = submitter.get('name')
        form.submitterfirst.data = submitter_name.get('first','')
        form.submitterlast.data = submitter_name.get('last','')
        form.submitteremail.data = submitter.get('email','')

        # Assertions other than markers
        assertions = dictsenlib.get('assertions')


    return render_template('edit.html', form=form)










