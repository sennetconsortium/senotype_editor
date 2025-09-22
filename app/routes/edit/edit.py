"""
Senotype edit route.
Works with editform.py.

"""

from flask import Blueprint, request, render_template, session

# WTForms
from models.editform import EditForm

# Helper classes
from models.appconfig import AppConfig
from models.senlib import SenLib

from models.formdata import (fetchfromdb, setdefaults, getmarkerobjects,
                             getcitationobjects, getoriginobjects, getdatasetobjects,
                             truncateddisplaytext)

edit_blueprint = Blueprint('edit', __name__, url_prefix='/edit')


def build_session_list(senlib: SenLib, form_data: dict, listkey: str):
    """
    Builds content for lists of assertions other than markers (taxon, location, etc.)
    on the Edit Form based on session data.
    :param senlib: SenLib interface object from which to obtain valueset information.
    :param form_data: dict of form state data.
    :param listkey: asser
    """

    assertion_map = {
        'taxon': 'in_taxon',
        'location': 'located_in',
        'celltype': 'has_cell_type',
        'hallmark': 'has_hallmark',
        'observable': 'has_molecular_observable',
        'inducer': 'has_inducer',
        'assay': 'has_assay',
        'citation': 'has_citation',
        'origin': 'has_origin',
        'dataset': 'has_dataset'
    }

    codelist = form_data[listkey]
    assertion = assertion_map[listkey]
    valueset = senlib.getsenlibvalueset(predicate=assertion)
    objects = {}
    if len(codelist) > 0:
        # Obtain the term for each code from the valueset for the associated assertion.
        # Externally linked lists (e.g., citation) will not be in valuesets.
        rawobjects = [
            {
                "code": item,
                "term": (
                    "" if assertion in ['has_citation', 'has_origin', 'has_dataset']
                    else valueset[valueset['valueset_code'] == item]['valueset_term'].iloc[0]
                )
            }
            for item in codelist
        ]

        # Obtain the appropriate term. Externally linked lists must obtain terms via API calls.
        if assertion == 'has_citation':
            objects = getcitationobjects(rawobjects)
        elif assertion == 'has_origin':
            objects = getoriginobjects(rawobjects)
        elif assertion == 'has_dataset':
            objects = getdatasetobjects(rawobjects)
        else:
            objects = rawobjects

    return objects


def build_session_markerlist(form_data: dict) -> list:
    """
    Builds content for the specified marker list on the Edit Form based on session data.
    :param form_data: dict of form state data.
    """
    codelist = form_data['marker']
    rawobjects = []
    for code in codelist:
        rawobjects.append({'code': code})

    objects = getmarkerobjects(rawobjects=rawobjects)
    return objects


def build_session_regmarkerlist(form_data: dict) -> list:
    """
    Builds content for the regulating marker list on the Edit Form based on session data.
    :param form_data: dict of form state data.
    """

    regmarkers = form_data['regmarker']
    # Elements in regmarkers are dictionaries with format {'action': action, 'marker': marker}.

    regmarkerlist = []
    for rm in regmarkers:
        rawobject = [{"code": rm['marker'].strip()}]
        # Obtain description of marker via API call.
        obj = getmarkerobjects(rawobjects=rawobject)[0]
        obj['type'] = rm['action']
        regmarkerlist.append(obj)

    return regmarkerlist


def getsessiondata(senlib: SenLib, form:EditForm, form_data: dict):
    """
    Populates list inputs (categorical assertions; citations; origins; datasets; and markers)
    in the edit form with session data, corresponding to a submission that is
    in progress--i.e., not already stored in senlib.

    Because the user can edit list content via modal forms, the session content will, in
    general, be different from any existing data for the submission.

    :param senlib: the SenLib interface
    :param form: the Edit form
    :param form_data: the session data for the form inputs
    """

    # Senotype data
    form.senotypename.data = form_data['senotypename']
    form.senotypedescription.data = form_data['senotypedescription']
    form.doi.data = form_data['doi']

    # Submitter data
    form.submitterfirst.data = form_data['submitterfirst']
    form.submitterlast.data = form_data['submitterlast']
    form.submitteremail.data = form_data['submitteremail']

    # build_session_list returns a list of objects in format {"code":code, "term": term}.
    # Pass to WTForms process a string in format code (term), which matches what is obtained
    # from the load from existing data, and will be parsed properly by the _field_lists
    # Jinja macro.
    # Taxon
    taxonlist = build_session_list(senlib=senlib, form_data=form_data, listkey='taxon')
    if len(taxonlist) > 0:
        form.taxon.process(None, [f"{item['code']} ({item['term']})" for item in taxonlist])
    else:
        form.taxon.process(None, [''])

    # Location
    locationlist = build_session_list(senlib=senlib, form_data=form_data, listkey='location')
    if len(locationlist) > 0:
        form.location.process(None, [f"{item['code']} ({item['term']})" for item in locationlist])
    else:
        form.location.process(None, [''])

    # Cell type
    celltypelist = build_session_list(senlib=senlib, form_data=form_data, listkey='celltype')
    if len(celltypelist) > 0:
        form.celltype.process(None, [f"{item['code']} ({item['term']})" for item in celltypelist])
    else:
        form.celltype.process(None, [''])

    # Hallmark
    hallmarklist = build_session_list(senlib=senlib, form_data=form_data, listkey='hallmark')
    if len(hallmarklist) > 0:
        form.hallmark.process(None, [f"{item['code']} ({item['term']})" for item in hallmarklist])
    else:
        form.hallmark.process(None, [''])

    # Molecular observable
    observablelist = build_session_list(senlib=senlib, form_data=form_data, listkey='observable')
    if len(observablelist) > 0:
        form.observable.process(None, [f"{item['code']} ({item['term']})" for item in observablelist])
    else:
        form.observable.process(None, [''])

    # Inducer
    inducerlist = build_session_list(senlib=senlib, form_data=form_data, listkey='inducer')
    if len(inducerlist) > 0:
        form.inducer.process(None, [f"{item['code']} ({item['term']})" for item in inducerlist])
    else:
        form.inducer.process(None, [''])

    # Assay
    assaylist = build_session_list(senlib=senlib, form_data=form_data, listkey='assay')
    if len(assaylist) > 0:
        form.assay.process(None, [f"{item['code']} ({item['term']})" for item in assaylist])
    else:
        form.assay.process(None, [''])

    # Citation
    citationlist = build_session_list(senlib=senlib, form_data=form_data, listkey='citation')
    if len(citationlist) > 0:
        form.citation.process(None, [truncateddisplaytext(id=item['code'],
                                                          description=item['term'],
                                                          trunclength=40)
                                     for item in citationlist])
    else:
        form.citation.process(None, [''])

    # Origin
    originlist = build_session_list(senlib=senlib, form_data=form_data, listkey='origin')
    if len(originlist) > 0:
        form.origin.process(None, [truncateddisplaytext(id=item['code'],
                                                        description=item['term'],
                                                        trunclength=50)
                                   for item in originlist])
    else:
        form.origin.process(None, [''])

    # Dataset
    datasetlist = build_session_list(senlib=senlib, form_data=form_data, listkey='dataset')
    if len(datasetlist) > 0:
        form.dataset.process(None, [truncateddisplaytext(id=item['code'],
                                                         description=item['term'],
                                                         trunclength=50)
                                    for item in datasetlist])
    else:
        form.dataset.process(None, [''])

    # Specified markers
    markerlist = build_session_markerlist(form_data=form_data)
    if len(markerlist) > 0:
        form.marker.process(None, [truncateddisplaytext(id=item['code'],
                                                        description=item['term'],
                                                        trunclength=100)
                                   for item in markerlist])
    else:
        form.marker.process(None, [''])

    # Regulating markers. The field processing is different because regmarker is a
    # FieldList(FormField) instead of a simple FieldList.
    regmarkerlist = build_session_regmarkerlist(form_data=form_data)
    if len(regmarkerlist) > 0:
        form.regmarker.process(
            None,
            [
                {
                    "marker": truncateddisplaytext(id=item['code'], description=item['term'], trunclength=50),
                    "action": item['type']
                }
                for item in regmarkerlist
            ]
        )
    else:

        form.regmarker.process(None, [''])


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
        getsessiondata(senlib=senlib, form=form, form_data=form_data)

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
        setdefaults(form=form)

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
            # The user selected 'new'. Load an empty form.
            setdefaults(form=form)

            # Use the Globus authentication information to identify the submitter.
            form.submitterfirst.data = session['username'].split(' ')[0]
            form.submitterlast.data = session['username'].split(' ')[1]
            form.submitteremail.data = session['userid']

        else:
            # Load from existing data.
            fetchfromdb(id=id, senlib=senlib, form=form)

    selected_node_id = request.form.get('selected_node_id') or request.args.get('selected_node_id')
    # Pass to the edit form the tree of senotype id information for the jstree control.
    return render_template('edit.html',
                           form=form,
                           response={'tree_data': senlib.senotypetree},
                           selected_node_id=selected_node_id)
