"""
Edit route.

"""
from flask import Blueprint, request, render_template, session

# The EditForm WTForm
from models.editform import EditForm

# Helper classes
from models.appconfig import AppConfig
from models.senlib import SenLib


edit_blueprint = Blueprint('edit', __name__, url_prefix='/edit')


@edit_blueprint.route('', methods=['POST', 'GET'])
def edit():

    # Clear any prior error messages that can display in the edit form.
    if 'flashes' in session:
        session['flashes'].clear()

    # Read the app.cfg file outside the Flask application context.

    cfg = AppConfig()

    # Get IDs for existing Senotype submissions.

    # Logic for using the senlib GitHub repo. (Deprecated)
    # Get the URLs to the senlib repo.
    # Base URL for the repo
    # senlib_url = cfg.getfield(key='SENOTYPE_URL')
    # URL to the Senotype Editor valueset CSV, stored in the senlib repo
    # valueset_url = cfg.getfield(key='VALUESET_URL')
    # URL to the folder for Senotype Submissions in the senlib repo
    # json_url = cfg.getfield(key='JSON_URL')
    # Github personal access token for authorized calls
    # github_token = cfg.getfield(key='GITHUB_TOKEN')

    # Senlib interface
    senlib = SenLib(cfg=cfg, userid=session['userid'])

    # Check if we have session data for the form.
    # Session data will correspond to the state of the form at the time of
    # validation errors resulting from an attempt at updating.
    # This form data represents either a new submission or modifications to an
    # existing submission.

    form_data = session.pop('form_data', None)
    form_errors = session.pop('form_errors', None)

    if form_data:
        # Populate the form with session data--i.e., the data for the submission that
        # the user is attempting to add or update.
        form = EditForm(data=form_data)
        senlib.getsessiondata(form=form, form_data=form_data)

        # Re-inject validation errors from the failed update.
        if form_errors:
            for field_name, errs in form_errors.items():
                if hasattr(form, field_name):
                    form_field = getattr(form, field_name)
                    form_field.errors = errs

    elif request.method == 'GET':

        # Initial load of the form as a result of the redirect from Globus login.
        # Load an empty form.
        form = EditForm()
        senlib.setdefaults(form=form)

    elif request.method == 'POST':

        # This is the result of a POST triggered by the change event in the senotype
        # list. In other words, the user selected something other than
        # 'new' in the list.
        # Fetch submission data from the senlib repo and populate the form.

        # Load existing data for the selected submission.
        form = EditForm(request.form)

        # Selected senotype id
        id = request.form.get('selected_node_id')

        if id == 'new' or id is None:

            # The user selected  'new' (for a new Senotype)
            # Load an empty form.
            senlib.setdefaults(form=form)

            # Mint a new SenNet ID.
            form.senotypeid.data = senlib.getnewsenotypeid()

            # Use the Globus authentication information to identify the submitter.
            form.submitterfirst.data = session['username'].split(' ')[0]
            form.submitterlast.data = session['username'].split(' ')[1]
            form.submitteremail.data = session['userid']

        else:
            # Load from existing data.
            senlib.fetchfromdb(id=id, form=form)

    selected_node_id = request.form.get('selected_node_id') or request.args.get('selected_node_id')
    # Pass to the edit form the tree of senotype id information for the jstree control.
    return render_template('edit.html',
                           form=form,
                           response={'tree_data': senlib.senotypetree},
                           selected_node_id=selected_node_id)
