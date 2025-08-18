"""
Senotype edit route.
Works with editform.py.

"""

from flask import Blueprint, request, render_template

# WTForms
from models.editform import EditForm

# Helper classes
from models.appconfig import AppConfig
from models.senlib import SenLib

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


def setdefaults(form):

    # Senotype and Submitter
    form.senotypename.data = ''
    form.senotypedescription.data = ''
    form.submitterfirst.data = ''
    form.submitterlast.data = ''
    form.submitteremail.data = ''

    # Simple assertions
    form.taxa.process([''])
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
    form.citations.process([''])
    form.origin.process([''])
    form.dataset.process([''])


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

    # Load the edit form and the edit page.
    form = EditForm(request.form)
    form.senotypeid.choices = choices

    if request.method == 'GET':
        # This is from the redirect from the login page.
        setdefaults(form=form)

    if request.method == 'POST': # and form.validate()

        # This is a result of the user selecting something other than 'new'
        # for a Senotype ID--i.e, an existing senotype. Load data.

        id = form.senotypeid.data

        print('original:', request.form.get('original_id', id))
        print('now:', form.senotypeid.data)

        if id == 'new':
            setdefaults(form=form)

        else:
            # User has selected another existing ID. Load from existing data.

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
                    form.taxa.process(form.taxa, [item['term'] for item in taxonlist])
                else:
                    form.taxa.process([''])
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
                    form.citations.process(form.citations, [item['code'] for item in citationlist])
                else:
                    form.citations.process([''])
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

    return render_template('edit.html', form=form)









