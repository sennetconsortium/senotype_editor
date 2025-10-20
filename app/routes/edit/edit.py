"""
Edit route:
1. Loads the Edit page with data from an existing Senotype.
2. Initiates a new Senotype, which will be written to the database via the Update route.

"""
from flask import Blueprint, request, render_template, session, make_response, abort, current_app
import json

# The EditForm WTForm
from models.editform import EditForm

# Helper classes
from models.appconfig import AppConfig
from models.senlib import SenLib

import logging

# Configure consistent logging. This is done at the beginning of each module instead of with a superclass of
# logger to avoid the need to overload function calls to logger.
logging.basicConfig(format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
                    level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

edit_blueprint = Blueprint('edit', __name__, url_prefix='/edit')


@edit_blueprint.route('', methods=['POST', 'GET'])
def edit():

    # Clear any prior error messages that can display in the edit form.
    if 'flashes' in session:
        session['flashes'].clear()

    # Read the app.cfg file outside the Flask application context.

    cfg = AppConfig()

    # Get IDs for existing Senotype submissions.

    # Senlib interface that fetches senotype data and builds the Senotype treeeview.
    senlib = SenLib(cfg=cfg, userid=session['userid'])

    # Cache the assertions valueset dataframe for use by routes like valueset.
    # The valueset dataframe should not change during the current editing transaction.
    current_app.assertionvaluesets = senlib.assertionvaluesets

    # Check if we have session data for the form.
    # The presence of session data corresponds to the state of the form at the time of
    # validation errors resulting from an attempt at updating.

    # This form data represents the edited state of either a new submission or modifications to an
    # existing submission.

    form_data = session.pop('form_data', None)
    form_errors = session.pop('form_errors', None)

    # Current state of the FTU paths input.
    ftu_tree_json = session.pop('ftu_tree_json', None)
    if ftu_tree_json:
        ftu_tree = json.loads(ftu_tree_json)
    else:
        ftu_tree = []
    senlib.ftutree = ftu_tree

    if form_data:
        # Populate the form with session data--i.e., the data for the submission that
        # the user is attempting to add or update.

        form = EditForm(data=form_data)
        senlib.getsessiondata(form=form, form_data=form_data)

        # Obtain information on the selected FTU path.

        # Re-inject validation errors from the failed update.
        if form_errors:
            for field_name, errs in form_errors.items():
                if hasattr(form, field_name):
                    form_field = getattr(form, field_name)
                    form_field.errors = errs

    elif request.method == 'GET':

        # This scenario occurs on the initial load of the form as a result of a
        # redirect--either from Globus login or from a failed update.

        # Load an empty form.
        form = EditForm()
        senlib.setdefaults(form=form)

    elif request.method == 'POST':

        # This is the result of a POST triggered by the change event in the senotype
        # treeview.  Fetch submission data from the senlib database if the
        # senotype already exists and populate the form.

        # Build the Edit form.
        form = EditForm(request.form)

        # Obtain the selected senotype id
        id = request.form.get('selected_node_id')

        if id == 'new' or id is None:

            # The user selected  'new' (for a new Senotype)
            # Load an empty form.
            senlib.setdefaults(form=form)

            # Mint a new SenNet ID.
            form.senotypeid.data = senlib.getnewsenotypeid()

            # Use the Globus authentication information to identify the submitter's
            # privileges. Currently, a user is only allowed to edit unpublished
            # senotypes for which the user's email matches the submitter email in
            # the senotype JSON.
            senlib.setuserassubmitter(form)

        else:
            # Load from existing data.
            senlib.fetchfromdb(senotypeid=id, form=form)

    selected_node_id = request.form.get('selected_node_id') or request.args.get('selected_node_id')

    # Pass to the edit form:
    # 1. the tree of senotype id information for the jstree control
    # 2. information for the complete 2D FTU jstree
    # 3. information for the senotype's FTU jstree
    return render_template('edit.html',
                           form=form,
                           response={'tree_data': senlib.senotypetree,
                                     'allftutree_data': current_app.allftutree,
                                     'ftu_tree_data': senlib.ftutree},
                           selected_node_id=selected_node_id)
