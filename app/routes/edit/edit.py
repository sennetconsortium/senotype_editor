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

from models.clearerrors import clearerrors

edit_blueprint = Blueprint('edit', __name__, url_prefix='/edit')


def getsimpleassertiondata(assertions: list, predicate: str) -> list:
    """
    Obtains information for the specified assertion from the Senotype submission
    JSON.
    :param assertions: list of assertion objects
    :param predicate: corresponds to predicate key

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

        objects = []
        if pred != '':
            objects = assertion.get('objects',[])
            return objects
    return []


def getcontextassertiondata(assertions: list, predicate: str, context: str) -> dict:
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

@edit_blueprint.route('', methods=['POST', 'GET'])
def edit():

    # Read the app.cfg file outside the Flask application context.
    cfg = AppConfig()

    # Get IDs for existing Senotype submissions.
    # Get the URLs to the senlib repo.
    senlib_url = cfg.getfield(key='SENOTYPE_URL')
    valueset_url = cfg.getfield(key='VALUESET_URL')
    json_url = cfg.getfield(key='JSON_URL')

    # Senlib interface
    senlib = SenLib(senlib_url, valueset_url, json_url)

    # Add 'new' as an option. Must be a tuple for correct display in the form.
    choices = [("new", "(new)")] + [(id, id) for id in senlib.senlibjsonids]

    if request.method == 'GET':
        # This is the result either of the redirect from Globus login or an
        # input validation error.

        form = EditForm()  # Empty form
        form.senotypeid.choices = choices
        setdefaults(form=form)

    if request.method == 'POST':
        # This is a result of the user selecting something other than 'new'
        # for a Senotype ID--i.e, an existing senotype. Load data.

        form = EditForm(request.form)
        form.senotypeid.choices = choices

        id = form.senotypeid.data
        print('id=',id)

        if id == 'new' or id is None:
            setdefaults(form=form)

        else:
            # User has selected another existing ID. Load from existing data.

            # Clear messages.
            if 'flashes' in session:
                session['flashes'].clear()
            clearerrors(form)

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

            # Taxon (multiple possible values)
            if id != request.form.get('original_id', id):
                # Load information from existing data.
                taxonlist = getsimpleassertiondata(assertions=assertions, predicate='in_taxon')
                if len(taxonlist) > 0:
                    form.taxon.process(form.taxon, [item['term'] for item in taxonlist])
                else:
                    form.taxon.process([''])
            else:
                # User triggered POST by managing the list (via Javascript).
                # WTForms has the information in request.forms
                pass

            # Locations (multiple possible values)
            if id != request.form.get('original_id', id):
                # Load information from existing data.
                locationlist = getsimpleassertiondata(assertions=assertions, predicate='located_in')
                if len(locationlist) > 0:
                    form.location.process(form.location, [item['term'] for item in locationlist])
                else:
                    form.location.process([''])
            else:
                # User triggered POST by managing the list (via Javascript).
                # WTForms has the information in request.forms
                pass

            # Cell type (one possible value)
            if id != request.form.get('original_id', id):
                # Load information from existing data.
                celltypelist = getsimpleassertiondata(assertions=assertions, predicate='has_cell_type')
                if len(celltypelist) > 0:
                    form.celltype.process(form.celltype, [item['term'] for item in celltypelist])
                else:
                    form.celltype.process([''])
            else:
                # User triggered POST by managing the list (via Javascript).
                # WTForms has the information in request.forms
                pass

            # Hallmark (multiple possible values)
            if id != request.form.get('original_id', id):
                # Load information from existing data.
                hallmarklist = getsimpleassertiondata(assertions=assertions, predicate='has_hallmark')
                if len(hallmarklist) > 0:
                    form.hallmark.process(form.hallmark, [item['term'] for item in hallmarklist])
                else:
                    form.hallmark.process([''])
            else:
                # User triggered POST by managing the list (via Javascript).
                # WTForms has the information in request.forms
                pass

            # Molecular observable (multiple possible values)
            if id != request.form.get('original_id', id):
                # Load information from existing data.
                observablelist = getsimpleassertiondata(assertions=assertions, predicate='has_molecular_observable')
                if len(observablelist) > 0:
                    form.observable.process(form.observable, [item['term'] for item in observablelist])
                else:
                    form.observable.process([''])
            else:
                # User triggered POST by managing the list (via Javascript).
                # WTForms has the information in request.forms
                pass

            # Inducer (multiple possible values)
            if id != request.form.get('original_id', id):
                # Load information from existing data.
                inducerlist = getsimpleassertiondata(assertions=assertions, predicate='has_inducer')
                if len(inducerlist) > 0:
                    form.inducer.process(form.inducer, [item['term'] for item in inducerlist])
                else:
                    form.inducer.process([''])
            else:
                # User triggered POST by managing the list (via Javascript).
                # WTForms has the information in request.forms
                pass

            # Assay (multiple possible values)
            if id != request.form.get('original_id', id):
                # Load information from existing data.
                assaylist = getsimpleassertiondata(assertions=assertions, predicate='has_assay')
                if len(assaylist) > 0:
                    form.assay.process(form.assay, [item['term'] for item in assaylist])
                else:
                    form.assay.process([''])
            else:
                # User triggered POST by managing the list (via Javascript).
                # WTForms has the  information in request.forms
                pass

            # Context assertions
            # Age
            age = getcontextassertiondata(assertions=assertions, predicate='has_context', context='age')
            if age != {}:
                form.agevalue.data = age.get('value', '')
                form.agelowerbound.data = age.get('lowerbound', '')
                form.ageupperbound.data = age.get('upperbound', '')
                form.ageunit.data = age.get('unit', '')

            # Citation (multiple possible values)

            if id != request.form.get('original_id', id):
                # Load citation information from existing data.
                citationlist = getsimpleassertiondata(assertions=assertions, predicate='has_citation')
                if len(citationlist) > 0:
                    form.citation.process(form.citation, [item['code'] for item in citationlist])
                else:
                    form.citation.process([''])
            else:
                # User triggered POST by managing the citation list (via Javascript).
                # WTForms has the citation information in request.forms
                pass

            # Origin (multiple possible values)
            if id != request.form.get('original_id', id):
                # Load origin information from existing data.
                originlist = getsimpleassertiondata(assertions=assertions, predicate='has_origin')
                if len(originlist) > 0:
                    form.origin.process(form.origin, [item['code'] for item in originlist])
                else:
                    form.origin.process([''])
            else:
                # User triggered POST by managing the list (via Javascript).
                # WTForms has the information in request.forms
                pass

            # Dataset (multiple possible values)
            if id != request.form.get('original_id', id):
                # Load dataset information from existing data.
                datasetlist = getsimpleassertiondata(assertions=assertions, predicate='has_dataset')
                if len(datasetlist) > 0:
                    form.dataset.process(form.dataset, [item['code'] for item in datasetlist])
                else:
                    form.dataset.process([''])
            else:
                # User triggered POST by managing the list (via Javascript).
                # WTForms has the information in request.forms
                pass

            # Specified Markers (multiple possible values)
            if id != request.form.get('original_id', id):
                # Load dataset information from existing data.
                markerlist = getsimpleassertiondata(assertions=assertions, predicate='has_characterizing_marker_set')
                if len(markerlist) > 0:
                    form.marker.process(form.marker, [item['symbol'] for item in markerlist])
                else:
                    form.marker.process([''])
            else:
                # User triggered POST by managing the list (via Javascript).
                # WTForms has the information in request.forms
                pass

            # Regulating Markers (multiple possible values)
            if id != request.form.get('original_id', id):
                # Load dataset information from existing data.
                regmarkerlist = getregmarkerdata(assertions=assertions)

                if len(markerlist) > 0:
                    form.regmarker.process(form.regmarker, [item['symbol'] for item in regmarkerlist])
                else:
                    form.regmarker.process([''])
            else:
                # User triggered POST by managing the list (via Javascript).
                # WTForms has the information in request.forms
                pass

    return render_template('edit.html', form=form)
