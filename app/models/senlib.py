"""
Class that serves as interface between the Edit form and the
Senotype submission JSON files in the senlib database.

Functions in the class:
1. Fetch data from the senlib database.
2. Hydrate senotype data with terms obtained from:
   a. the application valueset table in the database
   b. data from external sources via API calls
   c. the flask session


"""

from flask import session
import requests
import logging
import pandas as pd

# Application configuration object
from models.appconfig import AppConfig

# Interface to MySql database
from models.senlib_mysql import SenLibMySql

# Interface to GitHub repo (deprecated)
# from models.senlib_github import SenLibGitHub

# For external API requests
from models.requestretry import RequestRetry

# The EditForm
# from models.editform import EditForm

# Configure consistent logging. This is done at the beginning of each module instead of with a superclass of
# logger to avoid the need to overload function calls to logger.
logging.basicConfig(format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
                    level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


class SenLib:

    def _getsenotypejtree(self) -> dict:
        """
        Builds a JSON of annotated and grouped senotype IDs in jstree format, for use
        in the Senotype treeview in the Edit form.

        A senotype can have multiple versions. Each version of a senotype
        has a unique ID and senotype JSON.
        The senotype itself does not have a unique ID.

        The version of a particular senotype JSON is indicated by its
        provenance object, with keys that indicate the position of the
        senotype JSON in the provenance chain:
        - "predecessor" corresponds to the ID of the version that immediately
                        preceded the version in the JSON
        - "senotype"    corresponds to the ID of the version that succeeded the
                        version in the JSON

        The JSON of the "original version" of a senotype will have no predecessor.
        The JSON of the "latest version" of a senotype will have no successor.

        The provenance objects for all versions of a senotype correspond to
        a set of temporal relationships that proceed from earliest to latest.
        However, because only the latest version of a senotype is potentially
        editable, the treeview of senotypes represents versions in reverse
        temporal order, so that the depth of a senotype in the treeview represents
        the proximity to the original version of the senotype in the provenance chain.

        The versions of each senotype will be children of a "senotype" node
        that represents the senotype. The senotype node will share the name
        of the latest version of the senotype.

        There will also be:
        -- a "new" node for potential senotypes
        -- a parent for all senotype "root" nodes named "Senotype"

        This results in a "forest view" display for which each second level node
        (below "Senotype") represents an existing or potential senotype and
        lower level nodes represent provenance chains.

        Example:
        A senotype has 3 versions, with A followed by B followed by C. The latest
        senotype JSON for this senotype has name "X".

        The treeview will display:
        Senotype Library
        -- X
        ---- Version 3 (C)
        ------ Version 2 (B)
        -------- Version 1 (A)
        -- new

        The JSON has additional classes that the senotype-treeview Javascript uses
        to control treeview behavior:
        1. The "editable" class indicates whether the node corresponds to a senotype
           that has not yet been published.
        2. The "authorized" class indicates whether the user is authorized to
           edit a senotype. Authorization is based on the user's Globus userid.

        """

        # Node icons
        icon_locked = '🔒'
        icon_unauthorized = '🚫'
        icon_edit = '📝'

        # Obtain an (unordered) list of of all sentotype jsons.
        senotype_jsons = self.database._getallsenotypejsons()

        # Build maps used to organize senotypes by version:
        # All senotype IDs

        senotype_by_id = {}
        # Predecessors by ID
        predecessor_map = {}
        # Successors by ID
        successor_map = {}
        # Names by ID
        name_map = {}

        # Map every json in terms of provenance.
        # A provenance map element has key=ID of a JSON and value=ID of the predecessor
        # or successor--thus, "A":"B" in the successor map means that B precedes A.
        for obj in senotype_jsons:
            snt = obj["senotype"]
            id_ = snt["id"]
            name_map[id_] = snt.get("name", id_)
            senotype_by_id[id_] = snt
            prov = snt.get("provenance", {})
            pred = prov.get("predecessor")
            succ = prov.get("successor")
            if pred:
                predecessor_map[id_] = pred
            if succ:
                successor_map[id_] = succ

        # The root for a senotype corresponds to the id of its earliest
        # version--i.e., the JSON for which provenance does not indicate a predecessor.
        oldest_ids = [id_ for id_ in senotype_by_id if id_ not in predecessor_map]
        version_map = {}

        def assign_versions_from_oldest(id_, version):
            """
            Recursively calculate versions of senotype JSONs
            based on proximity to the oldest version, working from the oldest
            version forwards.
            """
            version_map[id_] = version
            succ = senotype_by_id[id_].get("provenance", {}).get("successor")
            if succ:
                # Recurse for children (later versions)
                assign_versions_from_oldest(succ, version + 1)

        for oid in oldest_ids:
            assign_versions_from_oldest(oid, 1)

        # BUILD THE TREE VIEW.

        # Build nodes for each senotype JSON.
        node_map = {}
        for id_ in senotype_by_id:
            snt = senotype_by_id[id_]

            # A senotype JSON can only be edited if it has not already been
            # published and assigned a DOI, and also not a folder.
            # The edit page uses this property to enable/disable editing features.
            editable = not bool(snt.get("doi"))

            # An editable JSON can only be edited by the original submitter.
            senotype_submitter_email = senotype_by_id[id_].get("submitter", {}).get("email")
            authorized = senotype_submitter_email == self.userid

            classes = []
            if editable:
                classes.append("editable")
            if authorized:
                classes.append("authorized")

            if editable and authorized:
                style = "color: green; font-weight: bold;"
                icon = icon_edit
                state = "editable"
            elif editable and not authorized:
                style = "color: red; font-weight: normal;"
                icon = icon_unauthorized
                state = "you are not unauthorized to edit"
            else:
                style = "color: gray; font-style: italic; font-weight: normal;"
                icon = icon_locked
                state = "published; read-only"

            instructions = f"Version {version_map[id_]} ({state})"
            a_attrs = {
                "class": " ".join(classes),
                "style": style,
                "title": instructions,
                "aria-label": instructions,
            }

            # Published nodes should be displayed as "disabled"--i.e., in gray
            # italic font. Folders, although not editable, should be displayed
            # with normal font.

            node_map[id_] = {
                "id": id_,
                "text": f"{icon} Version {version_map[id_]} ({id_})",
                "children": [],
                "state": {},
                "icon": "jstree-file",
                "a_attr": a_attrs,
            }

        # Attach children: each node is a child of its successor (reverse orientation)
        for id_, snt in senotype_by_id.items():
            succ = snt.get("provenance", {}).get("successor")
            if succ and succ in node_map:
                node_map[succ]["children"].append(node_map[id_])

        # Find root nodes (latest in chain: no successor)
        latest_ids = [
            id_ for id_ in senotype_by_id
            if "successor" not in senotype_by_id[id_].get("provenance", {})
               or not senotype_by_id[id_]["provenance"].get("successor")
        ]
        roots = [node_map[id_] for id_ in latest_ids]

        # Wrap each root with a "group" node.
        wrapped_roots = []
        for root in roots:
            version = version_map[root['id']]
            if int(version) > 1:
                versions = str(version) + ' versions'
            else:
                versions = str(version) + ' version'
            instructions = f"{name_map[root['id']]} ({versions}) - expand for details"
            wrapped_roots.append({
                "id": f"group{root['id']}", # name from latest version
                "text": instructions,
                "children": [root],
                # "state": {"opened": True},
                "state": {},
                "icon": "jstree-folder",  # folder icon
                "a_attr": {"style": "color: black; font-style: normal",
                           "title": instructions,
                           "aria-label": instructions},

            })

        # Add "new" node
        instructions = "Create a new senotype"
        a_attrs = {"class": "editable authorized",
                   "style": "color: green; font-style: bold",
                   "title": instructions,
                   "aria-label": instructions}

        new_node = {
            "id": "new",
            "text": f"{icon_edit} new",
            "children": [],
            "state": {},
            "icon": "jstree-file",
            "li_attr": {},
            "a_attr": a_attrs,
        }

        # Top-level "Senotype Library" node as parent
        instructions = ("Senotype Library: Expand and navigate to view existing senotypes, "
                        "create new versions of senotypes, and create new senotypes")
        senotype_parent = {
            "id": "Senotype",
            "text": "Senotype Library",
            "children": wrapped_roots + [new_node],
            "state": {"opened": True},
            "a_attr": {"style": "color: black; font-style: normal; font-size: 1.5em",
                       "title": instructions,
                       "aria-label": instructions},
        }

        return [senotype_parent]

    def getsenlibjson(self, id: str) -> dict:
        # Obtains the Senotype JSON for the specified ID.
        return self.database.getsenlibjson(id=id)

    def getassertionvalueset(self, predicate: str) -> pd.DataFrame:
        """
        Obtain the valueset associated with an assertion predicate.
        :param dfvaluesets: valueset dataframe
        :param predicate: assertion predicate. Can be either an IRI or a term.
        """

        df = self.assertionvaluesets

        # Check whether the predicate corresponds to an IRI.
        dfassertion = df[df['predicate_IRI'] == predicate]
        if len(dfassertion) == 0:
            # Check whether the predicate corresponds to a term.
            dfassertion = df[df['predicate_term'] == predicate]

        return dfassertion

    def getsenlibterm(self, predicate: str, code: str) -> str:
        """
        Returns the term from an assertion valueset for a code.
        :param predicate: assertion predicate for the valueset.
        :param code: code key
        """

        valueset = self.getassertionvalueset(predicate=predicate)
        matched = valueset.loc[valueset['valueset_code'] == code, 'valueset_term']
        term = matched.iloc[0] if not matched.empty else None

        return term

    def getdoi(self, senotype: dict) -> str:
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

    def getstoredsimpleassertiondata(self, assertions: list, predicate: str) -> list:
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
                    objects = self.getcitationobjects(rawobjects)
                elif pred == 'has_origin':
                    objects = self.getoriginobjects(rawobjects)
                elif pred == 'has_dataset':
                    objects = self.getdatasetobjects(rawobjects)
                elif pred == 'has_characterizing_marker_set':
                    objects = self.getmarkerobjects(rawobjects)
                else:
                    objects = self.getassertionobjects(pred=pred, rawobjects=rawobjects)
                return objects
        return []

    def getstoredsimpleassertiondata(self, assertions: list, predicate: str) -> list:
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
                    objects = self.getcitationobjects(rawobjects)
                elif pred == 'has_origin':
                    objects = self.getoriginobjects(rawobjects)
                elif pred == 'has_dataset':
                    objects = self.getdatasetobjects(rawobjects)
                elif pred == 'has_characterizing_marker_set':
                    objects = self.getmarkerobjects(rawobjects)
                else:
                    objects = self.getassertionobjects(pred=pred, rawobjects=rawobjects)
                return objects
        return []

    def getcitationobjects(self, rawobjects: list) -> list:

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

    def getstoredcontextassertiondata(self, assertions: list, predicate: str, context: str) -> dict:

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

    def truncateddisplaytext(self, id: str, description: str, trunclength: int) -> str:

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

    def getregmarkerobjects(self, assertions: list) -> list:

        """
        Obtains information related to the regulated markers of Senotype submission.
        :param assertions: list of assertions
        """

        listret = []
        for assertion in assertions:
            predicate = assertion.get('predicate')
            predicate_term = predicate.get('term')

            if predicate_term in ['up_regulates', 'down_regulates', 'inconclusively_regulates']:
                rawobjects = assertion.get('objects')
                listret = self.getmarkerobjects(rawobjects=rawobjects)

                for o in listret:
                    o['type'] = predicate_term

        return listret

    def getoriginobjects(self, rawobjects: list) -> list:

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

    def getdatasetobjects(self, rawobjects: list) -> list:

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
            title = dataset.get('title', '')
            oret.append({"code": code, "term": title})

        return oret

    def getmarkerobjects(self, rawobjects: list) -> list:

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

    def getassertionobjects(self, pred: str, rawobjects: list) -> list:

        """
        Reformats the objects array from a Senotype submission file for corresponding
        list in the edit form.
        :param rawobjects: list of assertion objects from a submission file.
        :param pred: assertion predicate

        """

        listret = []
        for o in rawobjects:
            code = o.get('code')
            term = self.getsenlibterm(predicate=pred, code=code)

            listret.append(
                {
                    'code': code,
                    'term': f'{code} ({term})'
                }
            )
            return listret

    def setdefaults(self, form):

        """
        Sets default values for the Edit form.
        :param form: the Edit form.
        """

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
        form.ageunit.data = 'year'

        # External assertions
        form.citation.process([''])
        form.origin.process([''])
        form.dataset.process([''])

        # Markers
        form.marker.process([''])
        form.regmarker.process([''])

    def fetchfromdb(self, id: str, form):

        """
        Loads and formats data from an existing Senotype submission, obtained
        from session data.

        :param id: senotype ID
        :param form: Edit Form

        """
        form.senotypeid.data = id

        # Get senotype data
        dictsenlib = self.getsenlibjson(id=id)

        senotype = dictsenlib.get('senotype')
        form.senotypename.data = senotype.get('name', '')
        form.senotypedescription.data = senotype.get('definition', '')
        form.doi.data = self.getdoi(senotype=senotype)

        # Submitter data
        submitter = dictsenlib.get('submitter', '')
        submitter_name = submitter.get('name', '')
        form.submitterfirst.data = submitter_name.get('first', '')
        form.submitterlast.data = submitter_name.get('last', '')
        form.submitteremail.data = submitter.get('email', '')

        # Assertions other than markers
        assertions = dictsenlib.get('assertions')

        # Taxon (multiple possible values)
        taxonlist = self.getstoredsimpleassertiondata(assertions=assertions, predicate='in_taxon')
        if len(taxonlist) > 0:
            form.taxon.process(form.taxon, [item['term'] for item in taxonlist])
        else:
            form.taxon.process([''])

        # Locations (multiple possible values)
        locationlist = self.getstoredsimpleassertiondata(assertions=assertions, predicate='located_in')
        if len(locationlist) > 0:
            form.location.process(form.location, [item['term'] for item in locationlist])
        else:
            form.location.process([''])

        # Cell type (one possible value)
        celltypelist = self.getstoredsimpleassertiondata(assertions=assertions, predicate='has_cell_type')
        if len(celltypelist) > 0:
            form.celltype.process(form.celltype, [item['term'] for item in celltypelist])
        else:
            form.celltype.process([''])

        # Hallmark (multiple possible values)
        hallmarklist = self.getstoredsimpleassertiondata(assertions=assertions, predicate='has_hallmark')
        if len(hallmarklist) > 0:
            form.hallmark.process(form.hallmark, [item['term'] for item in hallmarklist])
        else:
            form.hallmark.process([''])

        # Molecular observable (multiple possible values)
        observablelist = self.getstoredsimpleassertiondata(assertions=assertions,
                                                      predicate='has_molecular_observable')
        if len(observablelist) > 0:
            form.observable.process(form.observable, [item['term'] for item in observablelist])
        else:
            form.observable.process([''])

        # Inducer (multiple possible values)
        inducerlist = self.getstoredsimpleassertiondata(assertions=assertions, predicate='has_inducer')
        if len(inducerlist) > 0:
            form.inducer.process(form.inducer, [item['term'] for item in inducerlist])
        else:
            form.inducer.process([''])

        # Assay (multiple possible values)
        assaylist = self.getstoredsimpleassertiondata(assertions=assertions, predicate='has_assay')
        if len(assaylist) > 0:
            form.assay.process(form.assay, [item['term'] for item in assaylist])
        else:
            form.assay.process([''])

        # Context assertions
        # Age
        age = self.getstoredcontextassertiondata(assertions=assertions, predicate='has_context', context='age')
        if age != {}:
            form.agevalue.data = age.get('value', '')
            form.agelowerbound.data = age.get('lowerbound', '')
            form.ageupperbound.data = age.get('upperbound', '')
            form.ageunit.data = age.get('unit', '')

        # Citation (multiple possible values)
        citationlist = self.getstoredsimpleassertiondata(assertions=assertions, predicate='has_citation')
        if len(citationlist) > 0:
            form.citation.process(form.citation, [self.truncateddisplaytext(id=item['code'],
                                                                            description=item['term'],
                                                                            trunclength=40)
                                                  for item in citationlist])
        else:
            form.citation.process([''])

        # Origin (multiple possible values)
        originlist = self.getstoredsimpleassertiondata(assertions=assertions, predicate='has_origin')
        if len(originlist) > 0:
            form.origin.process(form.origin, [self.truncateddisplaytext(id=item['code'],
                                                                        description=item['term'],
                                                                        trunclength=40)
                                              for item in originlist])
        else:
            form.origin.process([''])

        # Dataset (multiple possible values)
        datasetlist = self.getstoredsimpleassertiondata(assertions=assertions, predicate='has_dataset')
        if len(datasetlist) > 0:
            form.dataset.process(form.dataset, [self.truncateddisplaytext(id=item['code'],
                                                                          description=item['term'],
                                                                          trunclength=40)
                                                for item in datasetlist])
        else:
            form.dataset.process([''])

        # Specified Markers (multiple possible values)
        markerlist = self.getstoredsimpleassertiondata(assertions=assertions,
                                                       predicate='has_characterizing_marker_set')
        if len(markerlist) > 0:
            form.marker.process(form.marker, [self.truncateddisplaytext(id=item['code'],
                                                                        description=item['term'],
                                              trunclength=100)
                                              for item in markerlist])
        else:
            form.marker.process([''])

        # Regulating Markers (multiple possible values).
        # The format of the process call is different because the regmarker
        # control is a FieldList(FormField) instead of just a Fieldlist.
        regmarkerlist = self.getregmarkerobjects(assertions=assertions)
        if len(regmarkerlist) > 0:
            form.regmarker.process(
                None,
                [
                    {
                        "marker": self.truncateddisplaytext(id=item['code'], description=item['term'],
                                                            trunclength=50),
                        "action": item['type']
                    }
                    for item in regmarkerlist
                ]
            )
        else:
            form.regmarker.process(None, [''])

    def getnewsenotypeid(self) -> str:
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

    def build_session_list(self, form_data: dict, listkey: str):
        """
        Builds content for lists of assertions other than markers (taxon, location, etc.)
        on the Edit Form based on session data.
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
        valueset = self.getassertionvalueset(predicate=assertion)
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
                objects = self.getcitationobjects(rawobjects)
            elif assertion == 'has_origin':
                objects = self.getoriginobjects(rawobjects)
            elif assertion == 'has_dataset':
                objects = self.getdatasetobjects(rawobjects)
            else:
                objects = rawobjects

        return objects

    def build_session_markerlist(self, form_data: dict) -> list:
        """
        Builds content for the specified marker list on the Edit Form based on session data.
        :param form_data: dict of form state data.
        """
        codelist = form_data['marker']
        rawobjects = []
        for code in codelist:
            rawobjects.append({'code': code})

        objects = self.getmarkerobjects(rawobjects=rawobjects)
        return objects

    def build_session_regmarkerlist(self, form_data: dict) -> list:
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
            obj = self.getmarkerobjects(rawobjects=rawobject)[0]
            obj['type'] = rm['action']
            regmarkerlist.append(obj)

        return regmarkerlist

    def getsessiondata(self, form, form_data: dict):
        """
        Populates list inputs (categorical assertions; citations; origins; datasets; and markers)
        in the edit form with session data, corresponding to a submission that is
        in progress--i.e., not already stored in senlib.

        Because the user can edit list content via modal forms, the session content will, in
        general, be different from any existing data for the submission.

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
        taxonlist = self.build_session_list(form_data=form_data, listkey='taxon')
        if len(taxonlist) > 0:
            form.taxon.process(None, [f"{item['code']} ({item['term']})" for item in taxonlist])
        else:
            form.taxon.process(None, [''])

        # Location
        locationlist = self.build_session_list(form_data=form_data, listkey='location')
        if len(locationlist) > 0:
            form.location.process(None, [f"{item['code']} ({item['term']})" for item in locationlist])
        else:
            form.location.process(None, [''])

        # Cell type
        celltypelist = self.build_session_list(form_data=form_data, listkey='celltype')
        if len(celltypelist) > 0:
            form.celltype.process(None, [f"{item['code']} ({item['term']})" for item in celltypelist])
        else:
            form.celltype.process(None, [''])

        # Hallmark
        hallmarklist = self.build_session_list(form_data=form_data, listkey='hallmark')
        if len(hallmarklist) > 0:
            form.hallmark.process(None, [f"{item['code']} ({item['term']})" for item in hallmarklist])
        else:
            form.hallmark.process(None, [''])

        # Molecular observable
        observablelist = self.build_session_list(form_data=form_data, listkey='observable')
        if len(observablelist) > 0:
            form.observable.process(None, [f"{item['code']} ({item['term']})" for item in observablelist])
        else:
            form.observable.process(None, [''])

        # Inducer
        inducerlist = self.build_session_list(form_data=form_data, listkey='inducer')
        if len(inducerlist) > 0:
            form.inducer.process(None, [f"{item['code']} ({item['term']})" for item in inducerlist])
        else:
            form.inducer.process(None, [''])

        # Assay
        assaylist = self.build_session_list(form_data=form_data, listkey='assay')
        if len(assaylist) > 0:
            form.assay.process(None, [f"{item['code']} ({item['term']})" for item in assaylist])
        else:
            form.assay.process(None, [''])

        # Citation
        citationlist = self.build_session_list(form_data=form_data, listkey='citation')
        if len(citationlist) > 0:
            form.citation.process(None, [self.truncateddisplaytext(id=item['code'],
                                                                   description=item['term'],
                                                                   trunclength=40)
                                         for item in citationlist])
        else:
            form.citation.process(None, [''])

        # Origin
        originlist = self.build_session_list(form_data=form_data, listkey='origin')
        if len(originlist) > 0:
            form.origin.process(None, [self.truncateddisplaytext(id=item['code'],
                                                                 description=item['term'],
                                                                 trunclength=50)
                                       for item in originlist])
        else:
            form.origin.process(None, [''])

        # Dataset
        datasetlist = self.build_session_list(form_data=form_data, listkey='dataset')
        if len(datasetlist) > 0:
            form.dataset.process(None, [self.truncateddisplaytext(id=item['code'],
                                                                  description=item['term'],
                                                                  trunclength=50)
                                        for item in datasetlist])
        else:
            form.dataset.process(None, [''])

        # Specified markers
        markerlist = self.build_session_markerlist(form_data=form_data)
        if len(markerlist) > 0:
            form.marker.process(None, [self.truncateddisplaytext(id=item['code'],
                                                                 description=item['term'],
                                                                 trunclength=100)
                                       for item in markerlist])
        else:
            form.marker.process(None, [''])

        # Regulating markers. The field processing is different because regmarker is a
        # FieldList(FormField) instead of a simple FieldList.
        regmarkerlist = self.build_session_regmarkerlist(form_data=form_data)
        if len(regmarkerlist) > 0:
            form.regmarker.process(None, [
                    {
                        "marker": self.truncateddisplaytext(id=item['code'], description=item['term'],
                                                            trunclength=50),
                        "action": item['type']
                    }
                    for item in regmarkerlist
                ]
            )
        else:
            form.regmarker.process(None, [])

    def getprovenanceids(self, senotypeid: str) -> dict:
        """
        Obtains the provenance ids for a senotype.
        :param senotypeid: senotype id
        """

        # If senotype exists in data, obtain provenance ids.
        senotypejson = self.getsenlibjson(id=senotypeid)
        if senotypejson != {}:
            dictprov = senotypejson.get('provenance')
            predecessor = dictprov.get('predecessor',None)
            successor = dictprov.get('successor', None)
        else:
            predecessor = None
            successor = None

        return {"provenance": {
            "predecessor": predecessor,
            "successor": successor
            }
        }

    def writesubmission(self, form_data: dict[str, str]) -> dict:
        """
        Builds a Senotype submission JSON from the POSTed request form data.
        :param form_data: inputs to write to the submission file.
        """

        dictsubmission = {}
        print(form_data)
        id = form_data.get('senotypeid')

        # senotype
        dictsenotype = {
            "id": id,
            "provenance": self.getprovenanceids(senotypeid=id),
            "doi": form_data.get('doiid-0',None),
            "name": form_data.get('senotypename'),
            "definition": form_data.get('senotypedescription')
        }

        # submitter
        dictsubmitter = {"name":
                             {"first": form_data.get('submitterfirst'),
                              "last": form_data.get('submitterlast')},
                         "email": form_data.get('submitteremail')
                         }

        dictsubmission = {"senotype": dictsenotype,
                          "submitter": dictsubmitter
                          }



        print(dictsubmission)
        exit(1)
        return dictsubmission

    def __init__(self, cfg: AppConfig, userid: str):

        """
        param cfg: AppConfig object representing the app.cfg file.
        userid: user Globus id

        The calling function will obtain the userid from the session store.

        """

        # Connect to the senlib database.
        # GitHub repo as a database has been deprecated.
        # self.database = SenLibGitHub(cfg)
        self.database = SenLibMySql(cfg)

        # Senotype Editor assertion valuesets
        self.assertionvaluesets = self.database.assertionvaluesets
        # Senotype Editor assertion-object maps

        self.userid = userid

        # JSON for the senotype jstree
        self.senotypetree = self._getsenotypejtree()

