"""
Data fetching functions common to edit and update routes.

"""

from flask import session
import requests

# WTForms
from models.editform import EditForm

from models.senlib import SenLib
from models.requestretry import RequestRetry
from models.appconfig import AppConfig


def getdoi(senotype: dict) -> str:
    """
    Calls the DataCite API to obtain the title for a DOI.
    :param senotype: senotype object of a senotype JSON
    """
    title = ''
    doi_url = senotype.get('doi', '')

    api = RequestRetry()

    if doi_url is None:
        return ''
    else:
        doi = doi_url.split('https://doi.org/')[1]
        url = f'https://api.datacite.org/dois/{doi}'
        response = api.getresponse(url=url, format='json')
        if response is not None:
            title = response.get('data').get('attributes').get('titles')[0].get('title', '')

        return f'{doi_url} ({title})'


def getstoredsimpleassertiondata(senlib: SenLib, assertions: list, predicate: str) -> list:
    """
    Obtains information for the specified assertion from a Senotype submission
    JSON.
    :param assertions: list of assertion objects
    :param predicate: assertion predicate key
    :param senlib: SenLib interface

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
                objects = getassertionobjects(senlib=senlib, pred=pred, rawobjects=rawobjects)
            return objects
    return []


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


def getstoredcontextassertiondata(assertions: list, predicate: str, context: str) -> dict:
    """
    Obtains information on a context assertion in a Senotype submission JSON.
    :param assertions: list of assertions
    :param predicate: assertion predicate
    :param context: type of context assertion
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
        if pred != '':
            objects = assertion.get('objects', [])
            for o in objects:
                objcontext = o.get('type')
                if objcontext == context:
                    return o

    return {}


def truncateddisplaytext(id: str, description:str, trunclength: int) -> str:
    """
    Builds a truncated display string.
    """
    if trunclength < 0:
        trunclength = len(description)
    if trunclength < len(description):
        ellipsis = '...'
    else:
        ellipsis = ''

    return f'{id} ({description[0:trunclength]}{ellipsis})'


def getregmarkerobjects(assertions: list) -> list:
    """
    Obtains information related to the regulated markers of Senotype submission.
    :param assertions: list of assertions
    """

    listret = []
    for assertion in assertions:
        predicate = assertion.get('predicate')
        predicate_term = predicate.get('term')

        if predicate_term in ['up_regulates','down_regulates','inconclusively_regulates']:
            rawobjects = assertion.get('objects')
            listret = getmarkerobjects(rawobjects=rawobjects)

            for o in listret:
                o['type'] = predicate_term

    return listret


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
        code = o.get('code').strip()
        if not code or ':' not in code:
            oret.append({"code": code, "term": None})
            continue
        markerid = code.split(':')[1]
        if 'HGNC' in code:
            endpoint = 'genes'
        else:
            endpoint = 'proteins'

        url = f'{base_url}{endpoint}/{markerid}'

        resp = api.getresponse(url=url, format='json')
        # Defensive: check if resp is a list and not empty
        if not resp or not isinstance(resp, list) or not resp[0]:
            term = code
        else:
            data = resp[0]
            if 'HGNC' in code:
                # For genes
                term = data.get('approved_symbol', code)
            else:
                # For proteins
                recommended_names = data.get('recommended_name')
                if isinstance(recommended_names, list) and recommended_names:
                    term = recommended_names[0].strip()
                else:
                    term = code
        oret.append({"code": code, "term": term})

    return oret


def getassertionobjects(senlib: SenLib, pred: str, rawobjects: list) -> list:
    """
    Reformats the objects array from a Senotype submission file for corresponding
    list in the edit form.
    :param rawobjects: list of assertion objects from a submission file.
    :param senlib: SenLib interface
    :param pred: assertion predicate

    """

    listret = []
    for o in rawobjects:
        code = o.get('code')
        term = senlib.getsenlibterm(predicate=pred, code=code)

        listret.append(
            {
                'code': code,
                'term': f'{code} ({term})'
            }
        )
        return listret


def setdefaults(form):

    # Senotype and Submitter
    form.senotypeid.data = ''
    form.senotypename.data = ''
    form.senotypedescription.data = ''
    form.doi.data = ''
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


def fetchfromdb(id: str, senlib: SenLib, form: EditForm):
    """
    Loads and formats data from an existing Senotype submission, obtained
    from stored data.

    """
    form.senotypeid.data = id

    # Get senotype data
    dictsenlib = senlib.getsenlibjson(id=id)

    senotype = dictsenlib.get('senotype')
    form.senotypename.data = senotype.get('name', '')
    form.senotypedescription.data = senotype.get('definition','')
    form.doi.data = getdoi(senotype=senotype)

    # Submitter data
    submitter = dictsenlib.get('submitter','')
    submitter_name = submitter.get('name','')
    form.submitterfirst.data = submitter_name.get('first', '')
    form.submitterlast.data = submitter_name.get('last', '')
    form.submitteremail.data = submitter.get('email', '')

    # Assertions other than markers
    assertions = dictsenlib.get('assertions')

    # Taxon (multiple possible values)
    taxonlist = getstoredsimpleassertiondata(senlib=senlib, assertions=assertions, predicate='in_taxon')
    if len(taxonlist) > 0:
        form.taxon.process(form.taxon, [item['term'] for item in taxonlist])
    else:
        form.taxon.process([''])

    # Locations (multiple possible values)
    locationlist = getstoredsimpleassertiondata(senlib=senlib, assertions=assertions, predicate='located_in')
    if len(locationlist) > 0:
        form.location.process(form.location, [item['term'] for item in locationlist])
    else:
        form.location.process([''])

    # Cell type (one possible value)
    celltypelist = getstoredsimpleassertiondata(senlib=senlib, assertions=assertions, predicate='has_cell_type')
    if len(celltypelist) > 0:
        form.celltype.process(form.celltype, [item['term'] for item in celltypelist])
    else:
        form.celltype.process([''])

    # Hallmark (multiple possible values)
    hallmarklist = getstoredsimpleassertiondata(senlib=senlib, assertions=assertions, predicate='has_hallmark')
    if len(hallmarklist) > 0:
        form.hallmark.process(form.hallmark, [item['term'] for item in hallmarklist])
    else:
        form.hallmark.process([''])

    # Molecular observable (multiple possible values)
    observablelist = getstoredsimpleassertiondata(senlib=senlib, assertions=assertions, predicate='has_molecular_observable')
    if len(observablelist) > 0:
        form.observable.process(form.observable, [item['term'] for item in observablelist])
    else:
        form.observable.process([''])

    # Inducer (multiple possible values)
    inducerlist = getstoredsimpleassertiondata(senlib=senlib, assertions=assertions, predicate='has_inducer')
    if len(inducerlist) > 0:
        form.inducer.process(form.inducer, [item['term'] for item in inducerlist])
    else:
        form.inducer.process([''])

    # Assay (multiple possible values)
    assaylist = getstoredsimpleassertiondata(senlib=senlib, assertions=assertions, predicate='has_assay')
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
    citationlist = getstoredsimpleassertiondata(senlib=senlib, assertions=assertions, predicate='has_citation')
    if len(citationlist) > 0:
        form.citation.process(form.citation, [truncateddisplaytext(id=item['code'],
                                                                   description=item['term'],
                                                                   trunclength=40)
                                              for item in citationlist])
    else:
        form.citation.process([''])

    # Origin (multiple possible values)
    originlist = getstoredsimpleassertiondata(senlib=senlib, assertions=assertions, predicate='has_origin')
    if len(originlist) > 0:
        form.origin.process(form.origin, [truncateddisplaytext(id=item['code'],
                                                               description=item['term'],
                                                               trunclength=40)
                                          for item in originlist])
    else:
        form.origin.process([''])

    # Dataset (multiple possible values)
    datasetlist = getstoredsimpleassertiondata(senlib=senlib, assertions=assertions, predicate='has_dataset')
    if len(datasetlist) > 0:
        form.dataset.process(form.dataset, [truncateddisplaytext(id=item['code'],
                                                                 description=item['term'],
                                                                 trunclength=40)
                                            for item in datasetlist])
    else:
        form.dataset.process([''])

    # Specified Markers (multiple possible values)
    markerlist = getstoredsimpleassertiondata(senlib=senlib, assertions=assertions, predicate='has_characterizing_marker_set')
    if len(markerlist) > 0:
        form.marker.process(form.marker, [truncateddisplaytext(id=item['code'],
                                                               description=item['term'],
                                                               trunclength=100)
                                          for item in markerlist])
    else:
        form.marker.process([''])

    # Regulating Markers (multiple possible values).
    # The format of the process call is different because the regmarker
    # control is a FieldList(FormField) instead of just a Fieldlist.
    regmarkerlist = getregmarkerobjects(assertions=assertions)
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


def getnewsenotypeid() -> str:
    """
    Calls the uuid-api to obtain a new SenNet ID.
    """

    # Get the URL to the uuid-api.
    cfg = AppConfig()
    uuid_url = f"{cfg.getfield(key='UUID_BASE_URL')}"

    # request body
    data = {"entity_type": "REFERENCE"}
    # auth header
    token = session["groups_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # The uuid-api returns a list of dicts. The default call returns one element.
    response = requests.post(url=uuid_url, headers=headers, json=data)
    responsejson = response.json()[0]
    sennet_id = responsejson.get('sennet_id', '')
    return sennet_id
