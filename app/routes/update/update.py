"""
Updates the Senotype repository by writing/overwriting a submission JSON file.
"""
from flask import Blueprint, request, render_template, flash, redirect, session, url_for
import uuid
from werkzeug.datastructures import MultiDict
import requests

# Helper classes
from models.appconfig import AppConfig
from models.senlib import SenLib
from models.editform import EditForm

from models.clearerrors import clearerrors

update_blueprint = Blueprint('update', __name__, url_prefix='/update')


def getnewsnid(uuid_base_url:str) -> str:
    """
    Obtain a new SenNet dataset ID from the uuid API.
    :param uuid_base_url: base URL to the uuid API.
    """

    data = {"entity_type":"REFERENCE"}

    try:
        response = requests.post(url=uuid_base_url, data=data)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        print("Status Code:", response.status_code)
        print("Response JSON:", response.json())
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

    return str(uuid.uuid4())


def buildsubmission(form_data: dict[str, str], uuid_base_url: str) -> dict:
    """
    Builds a Senotype submission JSON from the POSTed request form data.
    :param form_data: inputs to write to the submission file.
    :param uuid_base_url: base URL to the uuid API.
    """

    senotypeid = request.form.get('senotypeid')
    if senotypeid == 'new':
        senotypeid = getnewsnid(uuid_base_url=uuid_base_url)

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


def remove_duplicates_from_multidict(md: MultiDict, prefix_list: list) -> MultiDict:
    """
    Remove duplicate values for keys that start with any prefix in prefix_list.
    Keeps only unique values per prefix+value.
    """
    new_items = []
    seen = {}
    for key, value in md.items(multi=True):
        for prefix in prefix_list:
            if key.startswith(prefix):
                if (prefix, value) in seen:
                    break  # Already seen this value for this prefix
                seen[(prefix, value)] = True
        else:
            # Not a target prefix, always keep
            new_items.append((key, value))
            continue
        # If not break (i.e., not duplicate), save it
        if not (prefix, value) in seen:
            new_items.append((key, value))
    return MultiDict(new_items)


def validate_form(form, fieldlist_prefixes):
    """
    Custom validator that includes the hidden inputs passed to the update
    route by the update button on the Edit form.

    :param form: WTForms form instance
    :param fieldlist_prefixes: list of prefixes of hidden inputs built from modal forms
                               --e.g., ["taxon-", "location-"]
    :return: dict of errors
    """
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
            errors[base_name] = [f'At least one {errname} must be provided.']
    return errors


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
    uuid_base_url = cfg.getfield(key='UUID_BASE_URL')

    senlib = SenLib(senlib_url, valueset_url, json_url)

    # In the Edit form, the modal sections and Javascript build hidden text inputs
    # that store values added dynamically to lists in the assertion sections. For some
    # reason, the POST from the update button results in duplicate values.
    # In addition, the Edit form's default validators do not recognize the hidden
    # inputs.

    # List all fieldlist prefixes to deduplicate.
    fieldlist_prefixes= [
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

    deduped_form_data = remove_duplicates_from_multidict(request.form, fieldlist_prefixes)

    form = EditForm(deduped_form_data)  # Use POSTed form data

    # Set selected value for senotypeid (to preserve selection)
    prior_senotypeid = request.form.get('senotypeid', 'new')
    form.senotypeid.data = prior_senotypeid

    # Clear any prior error messages that can display in the edit form.
    if 'flashes' in session:
        session['flashes'].clear()

    # Apply custom validator of form data.
    custom_errors = validate_form(form=form, fieldlist_prefixes=fieldlist_prefixes)
    if len(custom_errors) == 0:
        # Handle successful update (save to database, etc.)
        dictsenotype = buildsubmission(form_data=deduped_form_data, uuid_base_url=uuid_base_url)
        writesubmission()
        flash('Success!')
        return redirect('/edit')
    else:
        # Inject custom errors into standard WTForms validation errors, avoiding duplicates.
        for field_name, custom_field_errors in custom_errors.items():
            if hasattr(form, field_name):
                form_field = getattr(form, field_name)
                for err in custom_field_errors:
                    if err not in form_field.errors:
                        form_field.errors.append(err)
        flash("Error: Validation failed. Please check your inputs.", "danger")
        # Pass both the current form data (which, in general, will have been modified
        # from the existing submission data) and the validation errors from the validated form
        # to a reload of the form.
        session['form_errors'] = form.errors
        session['form_data'] = form.data
        return redirect(url_for('edit.edit'))
