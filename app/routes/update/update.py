"""
Updates the Senotype repository by writing/overwriting a submission JSON file.
"""
from flask import Blueprint, request, render_template, flash, redirect, session, url_for, jsonify

from werkzeug.datastructures import MultiDict
import requests

# Helper classes
from models.appconfig import AppConfig
from models.senlib import SenLib
from models.editform import EditForm

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
        'observable-',
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
    return errors


@update_blueprint.route('', methods=['POST', 'GET'])
def update():
    """
    Receives POST from the update_form, which has all edit_form fields as hidden inputs (cloned by JS).
    Validates using WTForms and acts on result.
    """

    # Get IDs for existing Senotype submissions and URLs
    cfg = AppConfig()
    senlib = SenLib(cfg=cfg, userid=session['userid'])

    # Get the node that the user is attempting to create or update.
    id = request.form.get('selected_node_id') or request.args.get('selected_node_id')

    action = 'updat'
    if id == "new":
        # The edit route minted a new SenNet ID, which is in the senotypeid input.
        id = request.form.get('senotypeid')
        action = 'creat'

    # Normalize form data values of [''] and ['None'] to [].
    normalized_form_data = normalize_multidict(request.form)

    # Load the edit form with the deduplicated, normalized form data.
    form = EditForm(normalized_form_data)

    # Set selected value for senotypeid (to preserve selection)
    prior_senotypeid = request.form.get('senotypeid', 'new')
    form.senotypeid.data = prior_senotypeid

    # Clear any prior error messages that can display in the edit form.
    if 'flashes' in session:
        session['flashes'].clear()

    # Apply custom validator of form data.
    custom_errors = validate_form(form=form)

    if len(custom_errors) == 0:
        # Handle successful update (save to database, etc.)

        senlib.writesubmission(form_data=form.data)

        flash(f'Successfully {action}ed senotype with ID {id}.')

        # Trigger a reload of the edit form that refreshes with updated data.
        form = EditForm(request.form)
        senlib = SenLib(cfg=cfg, userid=session['userid'])

        senlib.fetchfromdb(id=id, form=form)

        return render_template('edit.html',
                               form=form,
                               response={'tree_data': senlib.senotypetree},
                               selected_node_id=id)

    else:
        # Inject custom errors into standard WTForms validation errors, avoiding duplicates.
        for field_name, custom_field_errors in custom_errors.items():
            if hasattr(form, field_name):
                form_field = getattr(form, field_name)
                for err in custom_field_errors:
                    if err not in form_field.errors:
                        form_field.errors.append(err)

        flash(f"Error: Validation failed during attempt to {action}e senotype with ID {id}. Please check your inputs.", "danger")

        # Pass both the current form data (which, in general, will have been modified
        # from the existing submission data) and the validation errors from the validated form
        # to a reload of the form.
        session['form_errors'] = form.errors
        session['form_data'] = form.data

        # Redirect to the edit form, which will set the focus of the treeview back
        # to the original node.
        selected_node_id = request.form.get('selected_node_id') or request.args.get('selected_node_id')
        return redirect(url_for('edit.edit', selected_node_id=selected_node_id))