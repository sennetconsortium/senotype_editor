"""
Senotype edit route.
Works with editform.py.

"""

from flask import Blueprint, request, render_template
from wtforms import SelectField, Field

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

    form.senotypename.data = ''
    form.senotypedescription.data = ''
    form.submitterfirst.data = ''
    form.submitterlast.data = ''
    form.submitteremail.data = ''
    form.taxon.data = 'select'
    form.location.data = 'select'
    form.celltype.data = 'select'
    form.observable.data = 'select'
    form.inducer.data = 'select'
    form.assay.data = 'select'
    form.agevalue.data = ''
    form.agelowerbound.data = ''
    form.ageupperbound.data = ''
    form.ageunit.data = ''


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
        if id == 'new':
            setdefaults(form=form)
        else:

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

            # Taxon (one possible value)
            taxa = getsimpleassertiondata(assertions=assertions, predicate='in_taxon')
            if len(taxa) > 0:
                form.taxon.data = taxa[0].get('code')
            else:
                form.taxon.data = 'select'

            # Location (one possible value)
            locations = getsimpleassertiondata(assertions=assertions, predicate='located_in')
            if len(locations) > 0:
                form.location.data = locations[0].get('code')
            else:
                form.location.data = 'select'

            # Cell type (one possible value)
            celltypes = getsimpleassertiondata(assertions=assertions, predicate='has_cell_type')
            if len(celltypes) > 0:
                form.celltype.data = celltypes[0].get('code')
            else:
                form.celltype.data = 'select'

            # Hallmark (one possible value)
            hallmarks = getsimpleassertiondata(assertions=assertions, predicate='has_hallmark')
            if len(hallmarks) > 0:
                form.hallmark.data = hallmarks[0].get('code')
            else:
                form.hallmark.data = 'select'

            # Molecular observable (one possible value)
            observables = getsimpleassertiondata(assertions=assertions, predicate='has_molecular_observable')
            if len(observables) > 0:
                form.observable.data = observables[0].get('code')
            else:
                form.observable.data = 'select'

            # Inducer (one possible value)
            inducers = getsimpleassertiondata(assertions=assertions, predicate='has_inducer')
            if len(inducers) > 0:
                form.inducer.data = inducers[0].get('code')
            else:
                form.inducer.data = 'select'

            # Assay (one possible value)
            assays = getsimpleassertiondata(assertions=assertions, predicate='has_assay')
            if len(assays) > 0:
                form.assay.data = assays[0].get('code')
            else:
                form.assay.data = 'select'

            # Context assertions
            # Age
            age = getcontextassertiondata(assertions=assertions, predicate='has_context', context='age')
            if age != {}:
                form.agevalue.data = age.get('value', '')
                form.agelowerbound.data = age.get('lowerbound', '')
                form.ageupperbound.data = age.get('upperbound', '')
                form.ageunit.data = age.get('unit', '')

    return render_template('edit.html', form=form)









