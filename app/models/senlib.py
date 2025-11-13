"""
Class that serves as interface between the Edit form and the
Senotype submission JSON files in the senlib database.

Functions in the class:
1. Fetch data from the senlib database.
2. Hydrate senotype data with terms obtained from:
   a. the application valueset table in the database
   b. data from external sources via API calls
   c. the flask session
3. Build the data used by the Senotype treeview control.
4. Write to the senlib database.


"""

from flask import session, current_app, request, abort
from werkzeug.datastructures import MultiDict
import requests
from requests.exceptions import ConnectionError
import logging
import pandas as pd


# Application configuration object
from models.appconfig import AppConfig

# Interface to MySql database
from models.senlib_mysql import SenLibMySql

# For external API requests
from models.requestretry import RequestRetry

# Configure consistent logging. This is done at the beginning of each module instead of with a superclass of
# logger to avoid the need to overload function calls to logger.
logging.basicConfig(format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
                    level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


class SenLib:

    def _getsenotypejtree(self) -> list[dict]:
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

        logging.info('Building senotype tree')

        # Node icons
        icon_locked = '🔒'
        icon_unauthorized = '🚫'
        icon_edit = '📝'

        # Obtain an (unordered) list of of all sentotype jsons.
        senotype_jsons = self.database.getallsenotypejsons()

        # Build maps used to organize senotypes by version:
        # All senotype IDs

        senotype_by_id = {}
        # Predecessors by ID
        predecessor_map = {}
        # Successors by ID
        successor_map = {}
        # Names by ID
        name_map = {}
        # Submitter emails by ID
        submitter_email_by_id = {}

        # Map every json in terms of provenance.
        # A provenance map element has key=ID of a JSON and value=ID of the predecessor
        # or successor--thus, "A":"B" in the successor map means that B precedes A.
        for obj in senotype_jsons:
            snt = obj["senotype"]
            id_ = snt["id"]
            name_map[id_] = snt.get("name", id_)
            senotype_by_id[id_] = snt
            submitter_email_by_id[id_] = obj.get("submitter").get("email")
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
            authorized = submitter_email_by_id[id_] == self.userid

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
        grouped_roots = []
        for root in roots:
            version = version_map[root['id']]
            if int(version) > 1:
                versions = str(version) + ' versions'
            else:
                versions = str(version) + ' version'
            instructions = f"{name_map[root['id']]} ({versions}) - expand for details"
            grouped_roots.append({
                "id": f"group{root['id']}",  # name from latest version
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
            "children": [new_node] + grouped_roots,
            "state": {"opened": True},
            "a_attr": {"style": "color: black; font-style: normal; font-size: 1.5em",
                       "title": instructions,
                       "aria-label": instructions},
        }

        return [senotype_parent]

    def getsenotypejson(self, id: str) -> dict:
        # Obtains the Senotype JSON for the specified ID.
        return self.database.getsenotypejson(id=id)

    def getassertionvalueset(self, predicate: str) -> pd.DataFrame:
        """
        Obtain the valueset associated with an assertion predicate.
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

            print(url)
            logger.info(f'Getting DataCite information for {doi}')

            response = api.getresponse(url=url, format='json')
            if response is None:
                urlheartbeat = 'https://api.datacite.org/heartbeat'
                responseheartbeat = api.getresponse(url=urlheartbeat)
                if responseheartbeat == 'OK':
                    title = 'unknown title'
                else:
                    title = 'invalid response from DataCite API'
            else:
                title = response.get('data').get('attributes').get('titles')[0].get('title', '')

            return f'{doi_url} ({title})'

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
                    logger.info('Getting information on specified markers from ontology API')
                    objects = self.getmarkerobjects(rawobjects)
                elif pred == 'has_cell_type':
                    objects = self.getcelltypeobjects(rawobjects)
                elif pred == 'located_in':
                    objects = self.getlocationobjects(rawobjects)
                elif pred == 'has_diagnosis':
                    objects = self.getdiagnosisobjects(rawobjects)
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

        logging.info('Getting citation data from NCBI EUtils')

        oret = []
        for o in rawobjects:
            code = o.get('code')
            pmid = code.split(':')[1]
            url = f'{base_url}{pmid}'
            citation = api.getresponse(url=url, format='json')
            result = citation.get('result')
            title = ''
            if result is None:
                title = "unknown"
            else:
                entry = result.get(pmid)
                if entry is None:
                    title = "unknown"
                else:
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

    def truncateddisplaytext(self, displayid: str, description: str, trunclength: int) -> str:

        """
        Builds a truncated display string.
        """
        if trunclength < 0:
            trunclength = len(description)
        if trunclength < len(description):
            ell = '...'
        else:
            ell = ''

        return f'{displayid} ({description[0:trunclength]}{ell})'

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
                logger.info('Getting information on regulating markers from ontology API')
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

        logger.info('Getting origin information from SciCrunch Resolver')

        oret = []
        for o in rawobjects:
            code = o.get('code')
            rrid = code.split(':')[1]
            url = f'{base_url}{rrid}.json'
            origin = api.getresponse(url=url, format='json')
            hits = origin.get('hits')
            if hits is None:
                description = "unknown"
            else:
                description = hits.get('hits')[0].get('_source').get('item').get('description', '')
            oret.append({"code": code, "term": description})

        return oret

    def getdatasetobjects(self, rawobjects: list) -> list:

        """
        Calls the entity API to obtain the description for the SenNet dataset.
        :param: rawobjects - a list of SenNet dataset objects.
        """
        api = RequestRetry()
        token = session['groups_token']
        headers = {"Authorization": f'Bearer {token}'}

        logger.info('Getting dataset information from SenNet entity-api')

        oret = []
        for o in rawobjects:
            code = o.get('code')
            snid = code
            url = f'{self.entity_url}{snid}'
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
        cfg = AppConfig()
        base_url = cfg.getfield('UBKG_BASE_URL')

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

            url = f'{base_url}/{endpoint}/{markerid}'

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

    def getcelltypeobjects(self, rawobjects: list) -> list:

        """
        Calls the UBKG API to obtain descriptions for cell types.
        :param: rawobjects - a list of cell type objects
        """
        api = RequestRetry()
        base_url = f"{request.host_url.rstrip('/')}/ontology/celltypes/"

        logger.info('Getting celltype information from ontology API')

        oret = []
        for o in rawobjects:
            code = o.get('code').split(':')[1]
            url = f'{base_url}{code}'
            celltype = api.getresponse(url=url, format='json')

            # celltypes returns a list of JSON objects
            if len(celltype) > 0:
                name = celltype[0].get('cell_type').get('name', '')
                oret.append({"code": f'CL:{code}', "term": name})
        return oret

    def getdiagnosisobjects(self, rawobjects: list) -> list:

        """
        Calls the UBKG API to obtain descriptions for diagnoses.
        :param: rawobjects - a list of diagnosis objects
        """
        api = RequestRetry()
        cfg = AppConfig()
        base_url = f"{request.host_url.rstrip('/')}/ontology/diagnoses/"

        logger.info('Getting diagnosis information from ontology API')

        oret = []
        for o in rawobjects:
            code = o.get('code')
            url = f'{base_url}{code}/code'
            diagnoses = api.getresponse(url=url, format='json')
            # diagnoses returns a list of JSON objects
            if len(diagnoses) > 0:
                term = diagnoses[0].get('term')
                oret.append({"code": code, "term": term})
        return oret

    def getlocationobjects(self, rawobjects: list) -> list:

        """
        Calls the UBKG API to obtain descriptions for organs.
        :param: rawobjects - a list of organ objects
        """
        api = RequestRetry()
        cfg = AppConfig()
        base_url = f"{request.host_url.rstrip('/')}/ontology/organs"

        logger.info('Getting organ information from ontology API')

        oret = []
        for o in rawobjects:
            code = o.get('code')
            url = f'{base_url}/{code}/code'
            organs = api.getresponse(url=url, format='json')
            # diagnoses returns a list of JSON objects
            if len(organs) > 0:
                term = organs[0].get('term')
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

    def _getnodetext(self, val: str) -> str:

        """
        Obtains the term for a senotype ftu jstree node from the allftu jstree.
        """

        allftutree = current_app.allftutree
        for organ in allftutree:
            organ_data = organ.get('data')
            if val == organ_data.get('value'):
                return organ.get('text')
            else:
                ftus = organ.get('children')
                for ftu in ftus:
                    ftu_data = ftu.get('data')
                    if val == ftu_data.get('value'):
                        return ftu.get('text')

                    ftuparts = ftu.get('children')
                    for ftupart in ftuparts:
                        ftupart_data = ftupart.get('data')
                        if val == ftupart_data.get('value'):
                            return ftupart.get('text')

    def buildftutree(self, assertions: list) -> list[dict]:
        """
        Builds an ftutree json from the 'has_ftu_path' assertions.
        :param assertions: assertion list from senotype

        FTU assertions are denormalized to the ftu part to allow for linking
        to different levels of the FTU hierarchy--e.g.,

        {"organ": "UBERON:XXXX",
        "ftu": "",
        "ftu_part": ""
        } for an organ

        {"organ": "UBERON:XXXX",
        "ftu": "UBERON:YYYY",
        "ftu_part": ""
        } for a FTU

        {"organ": "UBERON:XXXX",
        "ftu": "UBERON:YYYY",
        "ftu_part": "UBERON:ZZZZ" or "CL:AAAA"
        } for a FTU part

        The colon in codes is replaced with underscore to conform to IRIs in the
        2D FTU CSV.
        """

        iribase = 'http://purl.obolibrary.org/obo/'
        organs = {}
        for assertion in assertions:
            predicate = assertion.get('predicate').get('term')
            if predicate == 'has_ftu_path':
                objects = assertion.get('objects')

                for object in objects:
                    organ_val = object.get('organ').replace(':', '_')
                    ftu_val = object.get('ftu')
                    if ftu_val != '':
                        ftu_val = ftu_val.replace(':', '_')
                    ftu_part_val = object.get('ftu_part', '')
                    if ftu_part_val != '':
                        ftu_part_val = ftu_part_val.replace(':', '_')

                    if organ_val not in organs:
                        organs[organ_val] = {
                            "id": f"organ_{organ_val}",
                            "text": self._getnodetext(organ_val),
                            "data": {"value": organ_val, "iri": f"{iribase}{organ_val}"},
                            "children": {},
                            "state": {"opened": True}
                            }
                    organ_node = organs[organ_val]

                    # FTU node (under organ)
                    if ftu_val != '':
                        if ftu_val not in organ_node["children"]:
                            organ_node["children"][ftu_val] = {
                                "id": f"{organ_node['id']}_ftu_{ftu_val}",
                                "text": self._getnodetext(ftu_val),
                                "data": {"value": ftu_val, "iri": f"{iribase}{ftu_val}"},
                                "children": [],
                                "state": {"opened": True}
                            }
                        ftu_node = organ_node["children"][ftu_val]

                    # FTU Part node (under FTU).
                    if ftu_part_val != '':
                        ftu_node["children"].append({
                            "id": f"{ftu_node['id']}_part_{ftu_part_val}",
                            "text": self._getnodetext(ftu_part_val),
                            "data": {"value": ftu_part_val, "iri": f"{iribase}{ftu_part_val}"},
                            "state": {"opened": True}
                        })

                # Convert children dicts to lists for jsTree
                jstree = []
                for organ in organs.values():
                    organ['children'] = list(organ['children'].values())
                    jstree.append(organ)

                return jstree

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
        form.microenvironment.process([''])
        form.hallmark.process([''])
        form.inducer.process([''])
        form.assay.process([''])

        # Context assertions
        form.agevalue.data = ''
        form.agelowerbound.data = ''
        form.ageupperbound.data = ''
        form.ageunit.data = 'year'

        form.bmivalue.data = ''
        form.bmilowerbound.data = ''
        form.bmiupperbound.data = ''
        form.bmiunit.data = 'kg/m2'

        form.sex.process([''])

        # External assertions
        form.citation.process([''])
        form.origin.process([''])
        form.dataset.process([''])

        # Markers
        form.marker.process([''])
        form.regmarker.process([''])

        # future development
        # self.ftutree = []

        form.diagnosis.process([''])

    def fetchfromdb(self, senotypeid: str, form):

        """
        Loads and formats data from an existing Senotype submission, obtained
        from session data.

        :param senotypeid: senotype ID
        :param form: Edit Form

        """
        form.senotypeid.data = senotypeid

        # Get senotype data
        dictsenlib = self.getsenotypejson(id=senotypeid)
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

        # Taxon (valueset; multiple possible values)
        taxonlist = self.getstoredsimpleassertiondata(assertions=assertions, predicate='in_taxon')
        if len(taxonlist) > 0:
            form.taxon.process(form.taxon, [item['term'] for item in taxonlist])
        else:
            form.taxon.process([''])

        # Locations (external; multiple possible values)
        locationlist = self.getstoredsimpleassertiondata(assertions=assertions, predicate='located_in')
        if len(locationlist) > 0:
            form.location.process(form.location, [self.truncateddisplaytext(displayid=item['code'],
                                                                            description=item['term'],
                                                                            trunclength=50)
                                                  for item in locationlist])

        else:
            form.location.process([''])

        # Cell type (external; multiple values)
        celltypelist = self.getstoredsimpleassertiondata(assertions=assertions, predicate='has_cell_type')
        if len(celltypelist) > 0:
            form.celltype.process(form.celltype, [self.truncateddisplaytext(displayid=item['code'],
                                                                            description=item['term'],
                                                                            trunclength=100)
                                                  for item in celltypelist])
        else:
            form.celltype.process([''])

        # Microenvironment (valueset; multiple possible values)
        microenvironmentlist = self.getstoredsimpleassertiondata(assertions=assertions, predicate='has_microenvironment')
        if len(microenvironmentlist) > 0:
            form.microenvironment.process(form.microenvironment, [item['term'] for item in microenvironmentlist])
        else:
            form.microenvironment.process([''])

        # Hallmark (valueset; multiple possible values)
        hallmarklist = self.getstoredsimpleassertiondata(assertions=assertions, predicate='has_hallmark')
        if len(hallmarklist) > 0:
            form.hallmark.process(form.hallmark, [item['term'] for item in hallmarklist])
        else:
            form.hallmark.process([''])

        # Inducer (valueset; multiple possible values)
        inducerlist = self.getstoredsimpleassertiondata(assertions=assertions, predicate='has_inducer')
        if len(inducerlist) > 0:
            form.inducer.process(form.inducer, [item['term'] for item in inducerlist])
        else:
            form.inducer.process([''])

        # Assay (valueset; multiple possible values)
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
        form.ageunit.data = 'year'

        # BMI
        bmi = self.getstoredcontextassertiondata(assertions=assertions, predicate='has_context', context='BMI')
        if bmi != {}:
            form.bmivalue.data = bmi.get('value', '')
            form.bmilowerbound.data = bmi.get('lowerbound', '')
            form.bmiupperbound.data = bmi.get('upperbound', '')
        form.bmiunit.data = 'kg/m2'

        # sex
        sexlist = self.getstoredsimpleassertiondata(assertions=assertions, predicate='has_sex')
        if len(sexlist) > 0:
            form.sex.process(form.sex, [item['term'] for item in sexlist])
        else:
            form.sex.process([''])

        # Citation (external; multiple possible values)
        citationlist = self.getstoredsimpleassertiondata(assertions=assertions, predicate='has_citation')
        if len(citationlist) > 0:
            form.citation.process(form.citation, [self.truncateddisplaytext(displayid=item['code'],
                                                                            description=item['term'],
                                                                            trunclength=25)
                                                  for item in citationlist])
        else:
            form.citation.process([''])

        # Origin (multiple possible values)
        originlist = self.getstoredsimpleassertiondata(assertions=assertions, predicate='has_origin')
        if len(originlist) > 0:
            form.origin.process(form.origin, [self.truncateddisplaytext(displayid=item['code'],
                                                                        description=item['term'],
                                                                        trunclength=25)
                                              for item in originlist])
        else:
            form.origin.process([''])

        # Dataset (external; multiple possible values)
        datasetlist = self.getstoredsimpleassertiondata(assertions=assertions, predicate='has_dataset')
        if len(datasetlist) > 0:
            form.dataset.process(form.dataset, [self.truncateddisplaytext(displayid=item['code'],
                                                                          description=item['term'],
                                                                          trunclength=25)
                                                for item in datasetlist])
        else:
            form.dataset.process([''])

        # Specified Markers (external; multiple possible values)
        markerlist = self.getstoredsimpleassertiondata(assertions=assertions,
                                                       predicate='has_characterizing_marker_set')
        if len(markerlist) > 0:
            form.marker.process(form.marker, [self.truncateddisplaytext(displayid=item['code'],
                                                                        description=item['term'],
                                              trunclength=100)
                                              for item in markerlist])
        else:
            form.marker.process([''])

        # Regulating Markers (external; multiple possible values).
        # The format of the process call is different because the regmarker
        # control is a FieldList(FormField) instead of just a Fieldlist.
        regmarkerlist = self.getregmarkerobjects(assertions=assertions)
        if len(regmarkerlist) > 0:
            form.regmarker.process(
                None,
                [
                    {
                        "marker": self.truncateddisplaytext(displayid=item['code'], description=item['term'],
                                                            trunclength=50),
                        "action": item['type']
                    }
                    for item in regmarkerlist
                ]
            )
        else:
            form.regmarker.process(None, [''])

        # Future development:
        # Build an FTU treeview JSON from the ftupath data.
        # self.ftutree = self.buildftutree(assertions=assertions)

        # Diagnosis (external; multiple values)
        diagnosislist = self.getstoredsimpleassertiondata(assertions=assertions, predicate='has_diagnosis')

        if len(diagnosislist) > 0:
            form.diagnosis.process(form.diagnosis, [self.truncateddisplaytext(displayid=item['code'],
                                                                              description=item['term'],
                                                                              trunclength=50)
                                                    for item in diagnosislist])
        else:
            form.diagnosis.process([''])

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

    def get_field_metadata(self, field_name: str, field_property: str) -> str:
        """
        Returns a field from assertion_predicate_object for a form field.
        :param field_name: name of the field.
        :param field_property: name of an associated field in assertion_predicate_object
        """

        df = self.assertion_predicate_object

        matched = df[df['object_form_field'] == field_name][field_property]
        prop = matched.iloc[0] if not matched.empty else None
        return prop

    def get_iri(self, predicate_term: str) -> str:
        """
        Get the Relations Ontology IRI for an assertion predicate from the assertion
        valuesets.

        :param predicate_term: the predicate term
        """

        df = self.assertionvaluesets
        matched = df[df['predicate_term'] == predicate_term]['predicate_IRI']
        iri = matched.iloc[0] if not matched.empty else None
        return iri

    def build_session_list(self, form_data: dict, field_name: str):
        """
        Builds content for lists of assertions other than markers (taxon, location, etc.)
        on the Edit Form based on session data.
        :param form_data: dict of form state data.
        :param field_name: name of the field
        """

        # Get the assertion associated with the field in the form.
        assertion = self.get_field_metadata(field_name=field_name, field_property='predicate_term')
        # Get the valueset for the assertion.
        valueset = self.getassertionvalueset(predicate=assertion)

        # Get the list of codes associated with the field from the form.
        field_codelist = form_data[field_name]

        objects = {}
        if len(field_codelist) > 0:
            # Obtain the term for each code from the valueset for the associated assertion.
            # Externally linked lists (e.g., citation) will not be in valuesets.
            rawobjects = [
                {
                    "code": item,
                    "term": (
                        "" if assertion in ['has_citation', 'has_origin', 'has_dataset', 'has_cell_type',
                                            'has_diagnosis','located_in']
                        else valueset[valueset['valueset_code'] == item]['valueset_term'].iloc[0]
                    )
                }
                for item in field_codelist
            ]

            # Obtain the appropriate term. Externally linked lists must obtain terms via API calls.
            if assertion == 'has_citation':
                objects = self.getcitationobjects(rawobjects)
            elif assertion == 'has_origin':
                objects = self.getoriginobjects(rawobjects)
            elif assertion == 'has_dataset':
                objects = self.getdatasetobjects(rawobjects)
            elif assertion == 'has_cell_type':
                objects = self.getcelltypeobjects(rawobjects)
            elif assertion == 'located_in':
                objects = self.getlocationobjects(rawobjects)
            elif assertion == 'has_diagnosis':
                objects = self.getdiagnosisobjects(rawobjects)
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
        taxonlist = self.build_session_list(form_data=form_data, field_name='taxon')
        if len(taxonlist) > 0:
            form.taxon.process(None, [f"{item['code']} ({item['term']})" for item in taxonlist])
        else:
            form.taxon.process(None, [''])

        # Location
        locationlist = self.build_session_list(form_data=form_data, field_name='location')
        if len(locationlist) > 0:
            form.location.process(None, [f"{item['code']} ({item['term']})" for item in locationlist])
        else:
            form.location.process(None, [''])

        # Cell type
        celltypelist = self.build_session_list(form_data=form_data, field_name='celltype')

        if len(celltypelist) > 0:
            form.celltype.process(None, [self.truncateddisplaytext(displayid=item['code'],
                                                                   description=item['term'],
                                                                   trunclength=40)
                                         for item in celltypelist])
        else:
            form.celltype.process(None, [''])

        # Microenvironment
        microenvironmentlist = self.build_session_list(form_data=form_data, field_name='microenvironment')
        if len(microenvironmentlist) > 0:
            form.microenvironment.process(None, [f"{item['code']} ({item['term']})" for item in microenvironmentlist])
        else:
            form.microenvironment.process(None, [''])

        # Hallmark
        hallmarklist = self.build_session_list(form_data=form_data, field_name='hallmark')
        if len(hallmarklist) > 0:
            form.hallmark.process(None, [f"{item['code']} ({item['term']})" for item in hallmarklist])
        else:
            form.hallmark.process(None, [''])

        # Inducer
        inducerlist = self.build_session_list(form_data=form_data, field_name='inducer')
        if len(inducerlist) > 0:
            form.inducer.process(None, [f"{item['code']} ({item['term']})" for item in inducerlist])
        else:
            form.inducer.process(None, [''])

        # Assay
        assaylist = self.build_session_list(form_data=form_data, field_name='assay')
        if len(assaylist) > 0:
            form.assay.process(None, [f"{item['code']} ({item['term']})" for item in assaylist])
        else:
            form.assay.process(None, [''])

        # Citation
        citationlist = self.build_session_list(form_data=form_data, field_name='citation')
        if len(citationlist) > 0:
            form.citation.process(None, [self.truncateddisplaytext(displayid=item['code'],
                                                                   description=item['term'],
                                                                   trunclength=40)
                                         for item in citationlist])
        else:
            form.citation.process(None, [''])

        # Origin
        originlist = self.build_session_list(form_data=form_data, field_name='origin')
        if len(originlist) > 0:
            form.origin.process(None, [self.truncateddisplaytext(displayid=item['code'],
                                                                 description=item['term'],
                                                                 trunclength=50)
                                       for item in originlist])
        else:
            form.origin.process(None, [''])

        # Dataset
        datasetlist = self.build_session_list(form_data=form_data, field_name='dataset')
        if len(datasetlist) > 0:
            form.dataset.process(None, [self.truncateddisplaytext(displayid=item['code'],
                                                                  description=item['term'],
                                                                  trunclength=50)
                                        for item in datasetlist])
        else:
            form.dataset.process(None, [''])

        # Specified markers
        markerlist = self.build_session_markerlist(form_data=form_data)
        if len(markerlist) > 0:
            form.marker.process(None, [self.truncateddisplaytext(displayid=item['code'],
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
                        "marker": self.truncateddisplaytext(displayid=item['code'], description=item['term'],
                                                            trunclength=50),
                        "action": item['type']
                    }
                    for item in regmarkerlist
                ]
            )
        else:
            form.regmarker.process(None, [])

        diagnosislist = self.build_session_list(form_data=form_data, field_name='diagnosis')

        if len(diagnosislist) > 0:
            form.diagnosis.process(None, [self.truncateddisplaytext(displayid=item['code'],
                                                                    description=item['term'],
                                                                    trunclength=20)
                                          for item in diagnosislist])
        else:
            form.diagnosis.process(None, [''])

    def getprovenanceids(self, senotypeid: str, predecessorid: str) -> dict:
        """
        Obtains the provenance ids for a senotype.
        :param senotypeid: senotype id
        :param predecessorid: id of the predecessor of the senotype)
        """

        # If senotype exists in data, then the user requested either
        # the update of an existing senotype or the creation of a new version
        # of an existing senotype. If the senotype does not exist in data,
        # then the user requested the creation of a new senotype.

        senotypejson = self.getsenotypejson(id=senotypeid)

        if senotypejson != {}:
            # existing senotype
            senotype = senotypejson.get('senotype')
            dictprov = senotype.get('provenance')

            if predecessorid is None:
                # update of existing senotype
                predecessor = dictprov.get('predecessor', None)
            else:
                # new version of senotype
                predecessor = predecessorid

            successor = dictprov.get('successor', None)

        else:
            # new senotype
            predecessor = predecessorid
            successor = None

        return {
            "predecessor": predecessor,
            "successor": successor
            }

    def buildsimpleassertions(self, form_data: MultiDict) -> list:
        """
        Builds the elements of the assertions object of a senotype submission, corresponding
        to simple assertions--i.e., neither context assertions nor marker assertions.
        :param form_data: form data
        """

        # Loop through the keys of form_data that correspond to fields from the Edit
        # form with data.
        # For each field,
        # 1. Find the associated assertion predicate and source type.
        # 2. A field can have multiple values. Each field value corresponds to the object
        #    of an assertion. Build a list of "object" objects for each value.
        # 3. Associate the object list with the assertion information in an assertion object.
        # 4. Build a list of assertion objects.

        assertions = []
        for key in form_data:
            objects = []
            predicate_term = self.get_field_metadata(field_name=key, field_property='predicate_term')

            if predicate_term is None:
                # This is not a field that corresponds to an assertion.
                continue

            predicate_iri = self.get_iri(predicate_term=predicate_term)
            source = self.get_field_metadata(field_name=key, field_property='object_source')
            if isinstance(form_data.get(key), list):
                field_values = form_data.get(key)
            else:
                field_values = [form_data.get(key)]

            if len(field_values) > 0:

                for fv in field_values:
                    obj = {"source": source,
                           "code": fv}
                    objects.append(obj)

                if predicate_iri is not None:
                    predicate_object = {
                                        "term": predicate_term,
                                        "IRI": predicate_iri
                                    }
                else:
                    predicate_object = {
                        "term": predicate_term
                    }
                assertion = {"predicate": predicate_object,
                             "objects": objects
                             }
                assertions.append(assertion)

        return assertions

    def buildcontextassertions(self, form_data: MultiDict) -> list:
        """
        Builds the elements of the assertions object of a senotype submission, corresponding
        to context assertions.
        :param form_data: form data
        """

        # Get the context fields from context_assertion_code.
        # For each field,
        # - get
        #   - code (from context_assertion_code)
        #   - value, upperbound, lowerbound, unit - from form data

        # Assumption:
        # The value, upperbound, lowerbound, and unit associated with a context
        # assertion will all include the name of the assertion object--e.g.,
        # there will be an agevalue, ageupperbound, agelowerbound, and ageunit for
        # the context assertion object age.

        assertions = []

        df = self.context_assertion_code
        for index, row in df.iterrows():
            context_object_name = row['context_name']
            code = row['code']

            objects = []
            value = form_data.get(context_object_name)
            if value is not None:
                lowerbound_name = f'{context_object_name}lowerbound'
                lowerbound = form_data.get(lowerbound_name)
                upperbound_name = f'{context_object_name}upperbound'
                upperbound = form_data.get(upperbound_name)
                unit_name = f'{context_object_name}unit'
                unit = form_data.get(unit_name)
                obj = {
                    "term": context_object_name,
                    "code": code,
                    "value": value
                }
                if lowerbound is not None:
                    obj["lowerbound"] = lowerbound
                if upperbound is not None:
                    obj["upperbound"] = upperbound
                if unit is not None:
                    obj["unit"] = unit

                objects.append(obj)
                if len(objects) > 0:
                    predicate = {"term": "has_context"}
                    assertion = {"predicate": predicate,
                                 "objects": objects}
                    assertions.append(assertion)

            return assertions

    def buildregmarkerassertions(self, form_data: MultiDict) -> list:
        """
            Builds the elements of the assertions objects for
            regulating markers.
            :param form_data: form data
        """

        # Regulating markers must be distributed among the three types
        # of assertions--up_regulates, down_regulates, and inconclusively_regulates.
        # Aside from this sorting, the function is similar to buildsimpleassertions

        # For the regmarker field,
        # 1. The field can have multiple values. Each field value corresponds to the object
        #    of an assertion. Build a list of "object" objects for each value.
        # 2. Associate the object list with the assertion information in an assertion object.
        # 3. Build a list of assertion objects.

        assertions = []
        regmarkers = form_data.get('regmarker')

        if len(regmarkers) > 0:

            up_objects = []
            down_objects = []
            inc_objects = []

            for m in regmarkers:
                code = m.get('marker')
                action = m.get('action')
                obj = {"source": 'external',
                       "code": code}
                if action == 'up_regulates':
                    up_objects.append(obj)
                elif action == 'down_regulates':
                    down_objects.append(obj)
                else:
                    inc_objects.append(obj)

                if len(up_objects) > 0:
                    predicate = {"term": 'up_regulates'}
                    assertion = {"predicate": predicate,
                                 "objects": up_objects}
                    assertions.append(assertion)

                if len(down_objects) > 0:
                    predicate = {"term": 'down_regulates'}
                    assertion = {"predicate": predicate,
                                 "objects": down_objects}
                    assertions.append(assertion)

                if len(inc_objects) > 0:
                    predicate = {"term": 'inconclusively_regulates'}
                    assertion = {"predicate": predicate,
                                 "objects": inc_objects}
                    assertions.append(assertion)

        return assertions

    def buildftuassertions(self, ftu_tree: dict) -> list:
        """
        Build a set of assertions between the senotype and Functional Tissue Unit
        paths.
        :param ftu_tree: dict of FTU jstree information

        Assertion objects are denormalized to the level of ftu part to allow for selection
        at different levels of the hierarchy--e.g.,

        {"organ": "UBERON:XXXX",
        "ftu": "",
        "ftu_part": ""
        } for an organ

        {"organ": "UBERON:XXXX",
        "ftu": "UBERON:YYYY",
        "ftu_part": ""
        } for a FTU

        {"organ": "UBERON:XXXX",
        "ftu": "UBERON:YYYY",
        "ftu_part": "UBERON:ZZZZ" or "CL:AAAA"
        } for a FTU part

        """

        # Denormalize the tree node data at the level of ftu_part.
        ftu_paths = []
        for organ_node in ftu_tree:
            organ_code = organ_node['data']['value'].replace('_', ':')
            ftu_nodes = organ_node.get('children', [])
            if len(ftu_nodes) == 0:
                ftu_paths.append({
                    "organ": organ_code,
                    "ftu": "",
                    "ftu_part": ""
                })
            else:
                for ftu_node in organ_node.get('children', []):
                    ftu_code = ftu_node['data']['value'].replace('_', ':')
                    ftu_part_nodes = ftu_node.get('children', [])
                    if len(ftu_part_nodes) == 0:
                        ftu_paths.append({
                            "organ": organ_code,
                            "ftu": ftu_code,
                            "ftu_part": ""
                        })
                    else:
                        for part_node in ftu_node.get('children', []):
                            part_code = part_node['data']['value'].replace('_', ':')
                            ftu_paths.append({
                                "organ": organ_code,
                                "ftu": ftu_code,
                                "ftu_part": part_code
                            })

        predicate = {"term": "has_ftu_path"}
        assertions = [{"predicate": predicate,
                      "objects": ftu_paths}]

        return assertions

    # def buildassertions(self, form_data: MultiDict, ftu_tree: dict) -> list:
    def buildassertions(self, form_data: MultiDict) -> list:
        """
        Builds the assertions object of a senotype submission JSON
        :param form_data: form data
        :param ftu_tree: dict of FTU information
        """

        # Simple assertions, including specific markers
        assertions = self.buildsimpleassertions(form_data=form_data)

        # Regulating marker assertions
        assertions = assertions + self.buildregmarkerassertions(form_data=form_data)

        # Optional context assertions
        contextassertions = self.buildcontextassertions(form_data=form_data)
        if len(contextassertions) > 0:
            assertions = assertions + contextassertions

        # Future development:
        # FTU assertions
        # ftuassertions = self.buildftuassertions(ftu_tree=ftu_tree)
        # if len(ftuassertions) > 0:
            # assertions = assertions + ftuassertions

        return assertions

    # def buildsubmissionjson(self, form_data: MultiDict, senotypeid: str, predecessorid: str, ftu_tree: dict) -> dict:
    def buildsubmissionjson(self, form_data: MultiDict, senotypeid: str, predecessorid: str) -> dict:
        """
        Builds a Senotype submission JSON from the POSTed request form data.
        :param form_data: form data
        :param senotypeid: id of the senotype to build
        :param predecessorid: id of the predecessor of the senotype, for the case of
                              a new version
        :param ftu_tree: dict of FTU jstree information
        """

        # senotype

        # DOI
        # Parse the ID from the hydrated DOI field.
        doi = form_data.get('doi', None)
        if doi is not None:
            doiid = doi.split(' (')[0]
            doiurl = f'https://doi.org/{doiid}'
        else:
            doiurl = None

        dictsenotype = {
            "id": senotypeid,
            "provenance": self.getprovenanceids(senotypeid=senotypeid, predecessorid=predecessorid),
            "doi": doiurl,
            "name": form_data.get('senotypename'),
            "definition": form_data.get('senotypedescription')
        }

        # submitter
        dictname = {"first": form_data.get('submitterfirst'),
                    "last": form_data.get('submitterlast')}
        dictsubmitter = {"name": dictname,
                         "email": form_data.get('submitteremail')
                         }

        # assertions
        # listassertions = self.buildassertions(form_data=form_data, ftu_tree=ftu_tree)
        listassertions = self.buildassertions(form_data=form_data)

        dictsubmission = {"senotype": dictsenotype,
                          "submitter": dictsubmitter,
                          "assertions": listassertions
                          }

        return dictsubmission

    # def writesubmission(self, form_data: MultiDict, ftu_tree: dict, new_version_id: str = ''):
    def writesubmission(self, form_data: MultiDict, new_version_id: str = ''):
        """
        Writes a senotype submission to the senlib database.
        :param form_data: form data
        :param ftu_tree: dict of FTU jstree information.
        :param new_version_id: ID of the new version of an existing senotype.

        If new_version_id has a value, then a new version was requested.
        """

        if new_version_id == '':
            # Update existing senotype.
            senotypeid = form_data.get('senotypeid')
            predecessorid = None
        else:
            # Create a new version of the existing senotype.
            senotypeid = new_version_id
            predecessorid = form_data.get('senotypeid')

        # Build the submission JSON, with updates to provenance as necessary.
        # self.submissionjson = self.buildsubmissionjson(form_data=form_data, senotypeid=senotypeid,
                                                       # predecessorid=predecessorid, ftu_tree=ftu_tree)

        self.submissionjson = self.buildsubmissionjson(form_data=form_data, senotypeid=senotypeid,
                                                       predecessorid=predecessorid)

        # If this is a new version of an existing senotype, remove the DOI associated
        # with the predecessor version from the new version's data.
        if new_version_id != '':
            self.submissionjson['senotype']['doi'] = None

        # Write (upsert) the new submission record to the senlib database.
        self.database.writesenotype(senotypeid=senotypeid, senotypejson=self.submissionjson)

        # If this is a new version of an existing senotype, then update the provenance
        # of the penultimate version of the senotype, which is now the predecessor of the
        # new version.
        if new_version_id != '':
            self.updatesuccessor(senotypeid=predecessorid, successorid=new_version_id)

    def updatesuccessor(self, senotypeid: str, successorid: str):
        """
        Updates the successor for an existing senotype, for the case in which a
        new version of the senotype was requested.
        :param senotypeid: senotype to update
        :param successorid: new successor in provenance.

        """

        revisedjson = self.getsenotypejson(id=senotypeid)
        revisedjson['senotype']['provenance']['successor'] = successorid

        self.database.writesenotype(senotypeid=senotypeid, senotypejson=revisedjson)

    def setuserassubmitter(self, form):

        """
        Use the Globus authentication information to identify the user as the submitter.
        :param: form: the edit form
        """

        form.submitterfirst.data = session['username'].split(' ')[0]
        form.submitterlast.data = session['username'].split(' ')[1]
        form.submitteremail.data = session['userid']

    def getubkgstatus(self) -> str:

        """
        Check the status of the UBKG API.
        """
        api = RequestRetry()
        statusurl = self.cfg.getfield('UBKG_BASE_URL')

        try:
            status = api.getresponse(url=statusurl)
            if 'Hello!' in status:
                return 'OK'
            else:
                return 'NOT OK'

        except ConnectionError as e:
            abort(500, description=f'Error connecting to the UBKG API: {e}')

    def __init__(self, cfg: AppConfig, userid: str):

        """
        param cfg: AppConfig object representing the app.cfg file.
        userid: user Globus id

        The calling function will obtain the userid from the session store.

        """

        self.cfg = cfg
        # Base URL for calls to entity-api
        self.entity_url = self.cfg.getfield(key='ENTITY_BASE_URL')

        # Connect to the senlib database.
        self.database = SenLibMySql(cfg=self.cfg)

        # Senotype Editor assertion valuesets
        self.assertionvaluesets = self.database.assertionvaluesets

        # Cache the assertion valuesets at the app level
        # for use by routes like valueset
        current_app.assertionvaluesets = self.assertionvaluesets

        # Senotype Editor assertion-object maps
        self.assertion_predicate_object = self.database.assertion_predicate_object
        # Senotype Editor context maps
        self.context_assertion_code = self.database.context_assertion_code

        self.userid = userid

        # JSON for the senotype jstree
        self.senotypetree = self._getsenotypejtree()

        self.submissionjson = {}

        api = RequestRetry()
        urlheartbeat = 'https://api.datacite.org/heartbeat'
        self.datacitestatus = api.getresponse(url=urlheartbeat)
        logger.info(f'DataCite status = {self.datacitestatus}')

        self.ubkgstatus = self.getubkgstatus(cfg=cfg)
        logger.info(f'UBKG API status = {self.ubkgstatus}')
