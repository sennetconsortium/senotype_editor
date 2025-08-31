"""
Senotype edit route.
Works with editform.py.

"""

from flask import Blueprint, request, render_template, session
import pandas as pd

# WTForms
from models.editform import EditForm

# Helper classes
from models.appconfig import AppConfig
from models.senlib import SenLib
from models.requestretry import RequestRetry


edit_blueprint = Blueprint('edit', __name__, url_prefix='/edit')

def truncateddisplaytext(id: str, description:str, trunclength: int) -> str:
    """
    Builds a truncated display string.
    """
    if trunclength < 0:
        trunclength = len(description)

    return f'{id} ({description[0:trunclength]}...)'

def getcitationobjects(rawobjects: list) -> list:
    """
    Calls the NCBI EUtils API to obtain the title for the PMID.
    :param: rawobjects - a list of PMID objects.
    """
    api = RequestRetry()
    base_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id='

    oret = []
    for o in rawobjects:
        code = o.get('code')
        pmid = code.split(':')[1]
        url = f'{base_url}{pmid}'
        citation = api.getresponse(url=url, format='json')
        result = citation.get('result')
        title = ''
        if result is not None:
            entry = result.get(pmid)
            if entry is not None:
                title = entry.get('title', '')
        oret.append({"code": code, "term": title})

    return oret

def getoriginobjects(rawobjects: list) -> list:

    """
    Calls the SciCrunch API to obtain the title for the RRID.
    :param: rawobjects - the list of RRID objects.
    """
    api = RequestRetry()
    base_url = 'https://scicrunch.org/resolver/'

    oret = []
    for o in rawobjects:
        code = o.get('code')
        rrid = code.split(':')[1]
        url = f'{base_url}{rrid}.json'
        origin = api.getresponse(url=url, format='json')
        hits = origin.get('hits')
        if hits is not None:
            description = hits.get('hits')[0].get('_source').get('item').get('description', '')
        oret.append({"code": code, "term": description})

    return oret

def getdatasetobjects(rawobjects: list) -> list:

    """
    Calls the entity API to obtain the description for the SenNet dataset.
    :param: rawobjects - a list of SenNet dataset objects.
    """
    api = RequestRetry()
    base_url = 'https://entity.api.sennetconsortium.org/entities/'
    token = session['groups_token']
    headers = {"Authorization": f'Bearer {token}'}

    oret = []
    for o in rawobjects:
        code = o.get('code')
        snid = code
        url = f'{base_url}{snid}'
        dataset = api.getresponse(url=url, format='json', headers=headers)
        title = dataset.get('title','')
        oret.append({"code": code, "term": title})

    return oret

def getmarkerobjects(rawobjects: list) -> list:

    """
        Calls the entity API to obtain the description for specified markers.
        :param: rawobjects - a list of specified marker objects.
    """

    api = RequestRetry()
    base_url = 'https://ontology.api.hubmapconsortium.org/'

    oret = []
    for o in rawobjects:
        code = o.get('code')
        markerid = code.split(':')[1]
        if 'HGNC' in code:
            endpoint = 'genes'
        else:
            endpoint = 'proteins'

        url = f'{base_url}{endpoint}/{markerid}'
        print(url)
        dataset = api.getresponse(url=url, format='json')

        if 'HGNC' in code:
            term = dataset[0].get('approved_symbol', code)
        else:
            term = dataset[0].get('recommended_name', code)
            if term is not None:
                term = term[0].strip()

        oret.append({"code": code, "term": term})

    return oret

def getassertionobjects(rawobjects: list) -> list:
    """
    Reformats the objects array from a Senotype submission file for corresponding
    list in the edit form.
    :param rawobjects: list of assertion objects from a submission file.
    """

    listret = []
    for o in rawobjects:
        code = o.get('code')
        listret.append(
            {
                'code': code,
                'term': f'{code} ({o.get("term","")})'
            }
        )
        return listret

def getstoredsimpleassertiondata(assertions: list, predicate: str) -> list:
    """
    Obtains information for the specified assertion from a Senotype submission
    JSON.
    :param assertions: list of assertion objects
    :param predicate: assertion predicate key

    """

    for assertion in assertions:

        assertion_predicate = assertion.get('predicate')
        iri = assertion_predicate.get('IRI')
        term = assertion_predicate.get('term')
        pred = ''
        if iri == predicate:
            pred = predicate
        elif term == predicate:
            pred = predicate

        # Get descriptions for externally linked assertions (e.g., PMID) via API calls.
        objects = []
        if pred != '':
            rawobjects = assertion.get('objects', [])
            if pred == 'has_citation':
                objects = getcitationobjects(rawobjects)
            elif pred == 'has_origin':
                objects = getoriginobjects(rawobjects)
            elif pred == 'has_dataset':
                objects = getdatasetobjects(rawobjects)
            elif pred == 'has_characterizing_marker_set':
                objects = getmarkerobjects(rawobjects)
            else:
                objects = getassertionobjects(rawobjects)
            return objects
    return []


def getstoredcontextassertiondata(assertions: list, predicate: str, context: str) -> dict:
    """
    Obtains information on a context assertion in a Senotype submission JSON.
    :param assertions: list of assertions
    :param predicate: assertion predicate
    :param context: type of context assertion
    """

    for assertion in assertions:

        assertion_predicate = assertion.get('predicate')
        IRI = assertion_predicate.get('IRI')
        term = assertion_predicate.get('term')
        pred = ''
        if IRI == predicate:
            pred = predicate
        elif term == predicate:
            pred = predicate

        if pred != '':
            objects = assertion.get('objects',[])

            for o in objects:
                objcontext = o.get('term')
                if objcontext == context:
                    return o

    return {}

def getregmarkerdata(assertions: list) -> list:
    """
    Obtains information related to the markers of Senotype submission.
    :param assertions: list of assertions
    """

    listret = []
    for assertion in assertions:
        predicate = assertion.get('predicate')
        predicate_term = predicate.get('term')

        if predicate_term in ['up_regulates','down_regulates','inconclusively_regulates']:
            objects = assertion.get('objects')
            for o in objects:
                symbol = o.get('symbol')
                if predicate_term == 'up_regulates':
                    icon = '\u2191'
                elif predicate_term == 'down_regulates':
                    icon = '\u2193'
                else:
                    icon = '?'
                listret.append({'symbol': f'{symbol} \t {icon}'})

    return listret


def setdefaults(form):

    # Senotype and Submitter
    form.senotypename.data = ''
    form.senotypedescription.data = ''
    form.submitterfirst.data = ''
    form.submitterlast.data = ''
    form.submitteremail.data = ''

    # Simple assertions
    form.taxon.process([''])
    form.location.process([''])
    form.celltype.process([''])
    form.hallmark.process([''])
    form.observable.process([''])
    form.inducer.process([''])
    form.assay.process([''])

    # Context assertions
    form.agevalue.data = ''
    form.agelowerbound.data = ''
    form.ageupperbound.data = ''
    form.ageunit.data = ''

    # External assertions
    form.citation.process([''])
    form.origin.process([''])
    form.dataset.process([''])

    # Markers
    form.marker.process([''])
    form.regmarker.process([''])

def loadexistingdata(id: str, senlib: SenLib, form: EditForm):
    """
    Loads and formats data from an existing Senotype submission.

    """
    # Get senotype data
    dictsenlib = senlib.getsenlibjson(id=id)

    senotype = dictsenlib.get('senotype')
    form.senotypename.data = senotype.get('term', '')
    form.senotypedescription.data = senotype.get('definition')

    # Submitter data
    submitter = dictsenlib.get('submitter')
    submitter_name = submitter.get('name')
    form.submitterfirst.data = submitter_name.get('first', '')
    form.submitterlast.data = submitter_name.get('last', '')
    form.submitteremail.data = submitter.get('email', '')

    # Assertions other than markers
    assertions = dictsenlib.get('assertions')

    # Taxon (multiple possible values)
    taxonlist = getstoredsimpleassertiondata(assertions=assertions, predicate='in_taxon')
    if len(taxonlist) > 0:
        form.taxon.process(form.taxon, [item['term'] for item in taxonlist])
    else:
        form.taxon.process([''])

    # Locations (multiple possible values)
    locationlist = getstoredsimpleassertiondata(assertions=assertions, predicate='located_in')
    if len(locationlist) > 0:
        form.location.process(form.location, [item['term'] for item in locationlist])
    else:
        form.location.process([''])

    # Cell type (one possible value)
    celltypelist = getstoredsimpleassertiondata(assertions=assertions, predicate='has_cell_type')
    if len(celltypelist) > 0:
        form.celltype.process(form.celltype, [item['term'] for item in celltypelist])
    else:
        form.celltype.process([''])

    # Hallmark (multiple possible values)
    hallmarklist = getstoredsimpleassertiondata(assertions=assertions, predicate='has_hallmark')
    if len(hallmarklist) > 0:
        form.hallmark.process(form.hallmark, [item['term'] for item in hallmarklist])
    else:
        form.hallmark.process([''])

    # Molecular observable (multiple possible values)
    observablelist = getstoredsimpleassertiondata(assertions=assertions, predicate='has_molecular_observable')
    if len(observablelist) > 0:
        form.observable.process(form.observable, [item['term'] for item in observablelist])
    else:
        form.observable.process([''])

    # Inducer (multiple possible values)
    inducerlist = getstoredsimpleassertiondata(assertions=assertions, predicate='has_inducer')
    if len(inducerlist) > 0:
        form.inducer.process(form.inducer, [item['term'] for item in inducerlist])
    else:
        form.inducer.process([''])

    # Assay (multiple possible values)
    assaylist = getstoredsimpleassertiondata(assertions=assertions, predicate='has_assay')
    if len(assaylist) > 0:
        form.assay.process(form.assay, [item['term'] for item in assaylist])
    else:
        form.assay.process([''])

    # Context assertions
    # Age
    age = getstoredcontextassertiondata(assertions=assertions, predicate='has_context', context='age')
    if age != {}:
        form.agevalue.data = age.get('value', '')
        form.agelowerbound.data = age.get('lowerbound', '')
        form.ageupperbound.data = age.get('upperbound', '')
        form.ageunit.data = age.get('unit', '')

    # Citation (multiple possible values)
    citationlist = getstoredsimpleassertiondata(assertions=assertions, predicate='has_citation')
    if len(citationlist) > 0:
        form.citation.process(form.citation, [truncateddisplaytext(id=item['code'],
                                                                   description=item['term'],
                                                                   trunclength=70)
                                              for item in citationlist])
    else:
        form.citation.process([''])

    # Origin (multiple possible values)
    originlist = getstoredsimpleassertiondata(assertions=assertions, predicate='has_origin')
    if len(originlist) > 0:
        form.origin.process(form.origin, [truncateddisplaytext(id=item['code'],
                                                               description=item['term'],
                                                               trunclength=70)
                                          for item in originlist])
    else:
        form.origin.process([''])

    # Dataset (multiple possible values)
    datasetlist = getstoredsimpleassertiondata(assertions=assertions, predicate='has_dataset')
    if len(datasetlist) > 0:
        form.dataset.process(form.dataset, [truncateddisplaytext(id=item['code'],
                                                                 description=item['term'],
                                                                 trunclength=70)
                                            for item in datasetlist])
    else:
        form.dataset.process([''])

    # Specified Markers (multiple possible values)
    markerlist = getstoredsimpleassertiondata(assertions=assertions, predicate='has_characterizing_marker_set')
    if len(markerlist) > 0:
        form.marker.process(form.marker, [f'{item["code"]} ({item["term"]})' for item in markerlist])
    else:
        form.marker.process([''])

    # Regulating Markers (multiple possible values)
    regmarkerlist = getregmarkerdata(assertions=assertions)
    if len(markerlist) > 0:
        form.regmarker.process(form.regmarker, [item['symbol'] for item in regmarkerlist])
    else:
        form.regmarker.process([''])

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
        elif assertion == 'has_characterizing_marker_set':
            objects = getmarkerobjects(rawobjects)
        else:
            objects = rawobjects


    return objects

def build_session_markerlist(form_data: dict) -> list:
    """
    Builds content for the specified marker list on the Edit Form based on session data.
    :param form_data: dict of form state data.
    """
    print(form_data)
    codelist = form_data['marker']

    return []

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

    # Taxon
    taxonlist = build_session_list(senlib=senlib, form_data=form_data, listkey='taxon')
    if len(taxonlist) > 0:
        form.taxon.process(form.taxon, [item['term'] for item in taxonlist])
    else:
        form.taxon.process([''])

    # Location
    locationlist = build_session_list(senlib=senlib, form_data=form_data, listkey='location')
    if len(locationlist) > 0:
        form.location.process(form.location, [item['term'] for item in locationlist])
    else:
        form.location.process([''])

    # Cell type
    celltypelist = build_session_list(senlib=senlib, form_data=form_data, listkey='celltype')
    if len(celltypelist) > 0:
        form.celltype.process(form.celltype, [item['term'] for item in celltypelist])
    else:
        form.celltype.process([''])

    # Hallmark
    hallmarklist = build_session_list(senlib=senlib, form_data=form_data, listkey='hallmark')
    if len(hallmarklist) > 0:
        form.hallmark.process(form.hallmark, [item['term'] for item in hallmarklist])
    else:
        form.hallmark.process([''])

    # Molecular observable
    observablelist = build_session_list(senlib=senlib, form_data=form_data, listkey='observable')
    if len(observablelist) > 0:
        form.observable.process(form.hallmark, [item['term'] for item in observablelist])
    else:
        form.observable.process([''])

    # Inducer
    inducerlist = build_session_list(senlib=senlib, form_data=form_data, listkey='inducer')
    if len(inducerlist) > 0:
        form.inducer.process(form.hallmark, [item['term'] for item in inducerlist])
    else:
        form.inducer.process([''])

    # Assay
    assaylist = build_session_list(senlib=senlib, form_data=form_data, listkey='assay')
    if len(assaylist) > 0:
        form.assay.process(form.hallmark, [item['term'] for item in assaylist])
    else:
        form.assay.process([''])

    # Citation
    citationlist = build_session_list(senlib=senlib, form_data=form_data, listkey='citation')
    if len(citationlist) > 0:
        form.citation.process(form.citation, [truncateddisplaytext(id=item['code'],
                                                                   description=item['term'],
                                                                   trunclength=70)
                                              for item in citationlist])
    else:
        form.citation.process([''])

    # Origin
    originlist = build_session_list(senlib=senlib, form_data=form_data, listkey='origin')
    if len(originlist) > 0:
        form.origin.process(form.origin, [truncateddisplaytext(id=item['code'],
                                                                 description=item['term'],
                                                                 trunclength=70)
                                            for item in originlist])
    else:
        form.origin.process([''])

    # Dataset
    datasetlist = build_session_list(senlib=senlib, form_data=form_data, listkey='dataset')
    if len(datasetlist) > 0:
        form.dataset.process(form.dataset, [truncateddisplaytext(id=item['code'],
                                                                 description=item['term'],
                                                                 trunclength=70)
                                            for item in datasetlist])
    else:
        form.dataset.process([''])

    # Specified markers
    markerlist = build_session_markerlist(form_data=form_data)
    if len(markerlist) > 0:
        form.marker.process(form.marker, [truncateddisplaytext(id=item['code'],
                                                               description=item['term'],
                                                               trunclength=70)
                                          for item in markerlist])
    else:
        form.marker.process([''])


@edit_blueprint.route('', methods=['POST', 'GET'])
def edit():

    # Read the app.cfg file outside the Flask application context.

    cfg = AppConfig()

    # Get IDs for existing Senotype submissions.
    # Get the URLs to the senlib repo.
    # Base URL for the repo
    senlib_url = cfg.getfield(key='SENOTYPE_URL')
    # URL to the Senotype Editor valueset CSV, stored in the senlib repo
    valueset_url = cfg.getfield(key='VALUESET_URL')
    # URL to the folder for Senotype Submissions in the senlib repo
    json_url = cfg.getfield(key='JSON_URL')

    # Senlib interface
    senlib = SenLib(senlib_url, valueset_url, json_url)

    # Add 'new' as an option for the Senotype ID list.
    # Must be a tuple for correct display in the form.
    choices = [("new", "(new)")] + [(id, id) for id in senlib.senlibjsonids]

    print('edit')
    print('request.method', request.method)
    print('session', session)

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
        form.senotypeid.choices = choices  # includes "new"
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
        form.senotypeid.choices = choices # includes "new"
        setdefaults(form=form)

    elif request.method == 'POST':

        # This is the result of a POST triggered by the change event in the senotype
        # list. In other words, the user selected something other than
        # 'new' in the list.
        # Fetch submission data from the senlib repo and populate the form.

        # Load existing data for the selected submission.
        form = EditForm(request.form)
        form.senotypeid.choices = choices  # includes "new"

        id = form.senotypeid.data # Senotype submission id

        if id == 'new' or id is None:
            # The user selected 'new'. Load an empty form.
            setdefaults(form=form)

        else:
            # Load from existing data.
            loadexistingdata(id=id, senlib=senlib, form=form)

    return render_template('edit.html', form=form)
