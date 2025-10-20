"""
Updates the Senotype repository by writing/overwriting a submission JSON file.
"""
from flask import Blueprint, request, render_template, flash, redirect, session, url_for, current_app

from werkzeug.datastructures import MultiDict

import json

# Helper classes
from models.appconfig import AppConfig
from models.senlib import SenLib
from models.editform import EditForm

import logging

# Configure consistent logging. This is done at the beginning of each module instead of with a superclass of
# logger to avoid the need to overload function calls to logger.
logging.basicConfig(format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
                    level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

update_blueprint = Blueprint('update', __name__, url_prefix='/update')


def normalize_multidict(md: MultiDict) -> MultiDict:
    """
    Normalizes each field in a MultiDict:
    - For fields with multiple values: return a list of non-empty, stripped strings, excluding 'None' (string).
    - For fields with a single value: return the stripped string, not None.
    - Values of string 'None' or blank/whitespace are skipped.
    Returns a MultiDict (so .getlist() works).
    """

    normalized = MultiDict()
    for key in md.keys():
        values = md.getlist(key)
        # Remove empty strings, whitespace, and string 'None'
        cleaned = [v.strip() for v in values if v and v.strip() and v.strip() != 'None']
        if cleaned:
            for entry in cleaned:
                normalized.add(key, entry)

    return normalized


def validate_form(form):
    """
    Custom validator that includes the hidden inputs passed to the update
    route by the update button on the Edit form.

    :param form: WTForms form instance
    :return: dict of errors
    """

    fieldlist_prefixes = [
        'taxon-',
        'location-',
        'celltype-',
        'hallmark-',
        'inducer-',
        'assay-',
        'citation-',
        'origin-',
        'dataset-',
        'marker-',
        'regmarker-'
    ]
    errors = {}

    # Standard validation of inputs not populated via modal forms.
    if not form.validate():
        errors.update(form.errors)

    # Now check that each prefix has at least one non-empty value in form.data (request.form)
    # form.data is a dict of {fieldname: value}
    # form._fields contains all Field objects

    # For each prefix, look for keys in form.data that start with prefix and have a non-empty value
    formdata = getattr(form, 'data', {})
    for prefix in fieldlist_prefixes:
        # FieldList field base name, e.g. "taxon"
        base_name = prefix.rstrip('-')
        # Find all keys in formdata that start with prefix and have a value
        found = False
        for key in formdata:
            if key.startswith(base_name):
                val = formdata[key]
                if val not in [None, '', [], {}]:
                    found = True
                    break
        # If not found, add error.
        if not found:
            if base_name == 'marker':
                errname = 'specified marker'
            elif base_name == 'regmarker':
                errname = 'regulating marker'
            else:
                errname = base_name
            errors[base_name] = [f'At least one {errname} required.']

    # Verify that at least one FTU path was selected in the jstree.
    ftu_tree_json = form.ftu_tree_json.data
    if ftu_tree_json == '[]':
        errors['ftu_tree_json'] = ['At least one ftu path must be selected.']
    return errors


@update_blueprint.route('', methods=['POST', 'GET'])
def update():
    """
    Receives POST from the Update form, which has all edit_form fields as hidden inputs (cloned by JS).
    Validates using WTForms and acts on result.
    """

    # Get IDs for existing Senotype submissions and URLs
    cfg = AppConfig()
    senlib = SenLib(cfg=cfg, userid=session['userid'])

    # IDENTIFY THE SENOTYPE VERSION TO CREATE OR UPDATE
    # Information on the version is written to the hidden input named selected_node_id.

    # The user sets the value of the selected_node_id input through one of three paths:
    # 1. The user selects the node for an existing version in the treeview and then clicks
    #    the update/create button.
    #    Action: Update the senotype json for the existing version.
    # 2. The user selects "new" in the treeview and then clicks the update/create button.
    #    The Edit form created a senotype ID for the new senotype and stored it in the
    #    senotypeid input.
    #    Action: Create a new senotype record.
    # 3. The user selects an existing version and then clicks the "new version" button.
    #    The selected_node_id will concatenate the ID of the existing version with "_newversion"
    #    Actions:
    #    a. Create a new senotype record for the new version, based on the data from
    #       the existing version (except for the DOI).
    #    b. Update the provenance of the existing version to reflect that is is now the
    #       penultimate version of the senotype.

    selected_node_id = request.form.get('selected_node_id') or request.args.get('selected_node_id')
    update_id = ''
    action = ''

    # result_action_root is used in the display text of the header div in the edit form. The
    # tense of the action's verb is set based on the state of the action.
    result_action_root = ''

    isnewversion = False

    if selected_node_id == 'new':
        # The edit route minted a new SenNet ID, which is in the senotypeid input.
        update_id = request.form.get('senotypeid')
        result_action_root = 'creat'
    else:
        # Either update an existing or create a new version. Both actions are technically
        # updates to the existing version.
        result_action_root = 'updat'

        # Determine whether new version or simple update.
        action = request.form.get('action')
        if action == 'new_version':
            # Mint a new SenNet ID.
            update_id = senlib.getnewsenotypeid()
            isnewversion = True
        else:
            update_id = selected_node_id

    # PREPARE FORM DATA FOR SUBMISSION.
    # Normalize form data values of [''] and ['None'] to [].
    normalized_form_data = normalize_multidict(request.form)

    # Load the edit form with the normalized form data.
    form = EditForm(normalized_form_data)

    # If this is a new version, make sure that the current user is the submitter.
    if isnewversion:
        senlib.setuserassubmitter(form)

    # Clear any prior error messages.
    if 'flashes' in session:
        session['flashes'].clear()

    # VALIDATE INPUTS AND SUBMIT.

    # Apply custom validator of form data.
    custom_errors = validate_form(form=form)

    if len(custom_errors) == 0:

        # The submission data is valid.
        # Handle successful update.

        new_version_id = ''
        if action == 'new_version':
            new_version_id = update_id

        # Obtain information on the selected FTU path.
        ftu_tree_json = request.form.get('ftu_tree_json')
        if ftu_tree_json:
            ftu_tree = json.loads(ftu_tree_json)
        else:
            ftu_tree = []

        # Write to the database. If new_version_id has a value, then the writesubmission
        # script will also update the provenance of the penultimate version.
        senlib.writesubmission(form_data=form.data, new_version_id=new_version_id, ftu_tree=ftu_tree)

        flash(f'Successfully {result_action_root}ed senotype with ID {update_id}.')

        # Trigger a reload of the edit form that refreshes with the updated data.
        form = EditForm(request.form)
        senlib = SenLib(cfg=cfg, userid=session['userid'])
        senlib.fetchfromdb(senotypeid=update_id, form=form)

        # Pass to the edit form:
        # 1. the tree of senotype id information for the jstree control
        # 2. information for the complete 2D FTU jstree
        # 3. information for the senotype's FTU jstree
        return render_template('edit.html',
                               form=form,
                               response={'tree_data': senlib.senotypetree,
                                         'allftutree_data': current_app.allftutree,
                                         'ftu_tree_data': senlib.ftutree},
                               selected_node_id=update_id)

    else:
        # Inject custom errors into standard WTForms validation errors, avoiding duplicates.
        for field_name, custom_field_errors in custom_errors.items():
            if hasattr(form, field_name):
                form_field = getattr(form, field_name)
                for err in custom_field_errors:
                    if err not in form_field.errors:
                        form_field.errors.append(err)

        flash(f"Error: Validation failed during attempt to {result_action_root}e senotype with ID {update_id}. "
              f"Please check your inputs.", "danger")

        # Pass both the current form data (which, in general, will have been modified
        # from the existing submission data) and the validation errors from the validated form
        # to a reload of the form.
        session['form_errors'] = form.errors
        session['form_data'] = form.data

        # Get the state of the FTU path selection.
        session['ftu_tree_json'] = request.form.get('ftu_tree_json')

        # Redirect to the edit form, which will set the focus of the treeview back
        # to the original node.
        selected_node_id = request.form.get('selected_node_id') or request.args.get('selected_node_id')

        # Save FTU tree JSON to session for reload
        session['ftu_tree_json'] = request.form.get('ftu_tree_json')

        return redirect(url_for('edit.edit', selected_node_id=selected_node_id))
