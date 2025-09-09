"""
Class for working with Senotype submission JSON files in the senlib repository.
"""
import logging
import pandas as pd
from io import StringIO
import json

from models.requestretry import RequestRetry

# Configure consistent logging. This is done at the beginning of each module instead of with a superclass of
# logger to avoid the need to overload function calls to logger.
logging.basicConfig(format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
                    level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


class SenLib:

    def _getsenlibrepolist(self) -> list:
        """
        Obtains list of files in the senlib repo.
        """
        return self.request.getresponse(url=self.senliburl, format='json')

    def _getsenotypeids(self) -> list:
        """
        Obtains the ids of all Senotype submissions in the senlib repo.
        :return: list of Senotype ids
        """

        listdir = self._getsenlibrepolist()
        listids = []

        # The latest version of a Senotype will not have a successor.
        for entry in listdir:
            if entry != 'message':
                filename = entry.get('name')
                senotypeid = filename.split('.json')[0]
                senotypejson = self.getsenlibjson(senotypeid)
                senotype = senotypejson.get('senotype')
                provenance = senotype.get('provenance')
                successor = provenance.get('successor')
                name = senotype.get('name', '')
                if len(name) >= 50:
                    name = f'{name[0:47]}...'

                listids.append(f'{senotypeid} ({name})')

        return listids

    def _getallsenotypejsons(self) -> dict:
        """
        Obtains a list of all senotype jsons.
        """
        listdir = self._getsenlibrepolist()

        # First, get the latest versions of each senotype.
        # The latest version of a senotype will not have a successor.
        listjson = []
        for entry in listdir:
            filename = entry.get('name')
            senotypeid = filename.split('.json')[0]
            listjson.append(self.getsenlibjson(senotypeid))

        return listjson

    def _getsenotypejtree(self) -> dict:
        """
        Builds a JSON of senotype IDs in jstree format.

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
        Senotype
        -- X
        ---- Version 3 (C)
        ------ Version 2 (B)
        -------- Version 1 (A)
        -- new

        """

        # Obtain an (unordered) list of of all sentotype jsons.
        senotype_jsons = self._getallsenotypejsons()

        # Build maps used to organize senotypes by version:
        # All senotype IDs
        senotype_by_id = {}
        # Predecessors by ID
        predecessor_map = {}
        # Successors by ID
        successor_map = {}
        # Names by ID
        name_map = {}

        # Map every json in terms of provenanc.
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

        # Recursively calculate versions of senotype JSONs
        # based on proximity to the oldest version, working from the oldest
        # version forwards.

        def assign_versions_from_oldest(id_, version):
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
            # published and assigned a DOI. The edit page uses this property
            # to enable/disable editing features.
            editable = not bool(snt.get("doi"))

            node_map[id_] = {
                "id": id_,
                "text": f"Version {version_map[id_]} ({id_})",
                "children": [],
                "state": {},
                "icon": "jstree-file",
                "a_attr": {"class": "editable"} if editable else {},
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

        # Wrap each root with a "Senotype node".
        wrapped_roots = []
        for root in roots:
            name_only = name_map[root["id"]]
            wrapped_roots.append({
                "id": f"rootwrap_{root['id']}", # name from latest version
                "text": name_only,
                "children": [root],
                # "state": {"opened": True},
                "state": {},
                "icon": "jstree-folder",  # folder icon
                "a_attr": {}, # not editable
            })

        # Add "new" node
        new_node = {
            "id": "new",
            "text": "new",
            "children": [],
            "state": {},
            "icon": "jstree-file",
            "li_attr": {},
            "a_attr": {"class": "editable"},
        }

        # Top-level "Senotype" node as parent
        senotype_parent = {
            "id": "Senotype",
            "text": "Senotype",
            "children": wrapped_roots + [new_node],
            "state": {"opened": True}
        }

        return [senotype_parent]

    def getsenlibjson(self, id: str) -> dict:
        """
        Get a single senotype JSON.
        :param id: id of the senotype, corresponding to the file name in the data
                   source.
        :return: the senotype json
        """
        url = f'{self.jsonurl}/{id}.json'
        return self.request.getresponse(url=url, format='json')

    def _getsenlibvaluesets(self) -> pd.DataFrame:
        """
        Get the Senotype Editor valueset from the senlib repo as a Pandas DataFrame.
        :return:
        """

        # Get the text stream from GitHub.
        stream=self.request.getresponse(url=self.valueseturl, format='csv')
        # Convert to a string.
        csv_data = StringIO(stream)
        # Read into Pandas.
        return pd.read_csv(csv_data)

    def __init__(self, senliburl: str, valueseturl: str, jsonurl: str):

        self.request = RequestRetry()

        # Obtain list of senlib JSONs.
        self.senliburl = senliburl
        self.valueseturl = valueseturl
        self.jsonurl = jsonurl
        self.senlibjsonids = self._getsenotypeids()
        self.senlibvaluesets = self._getsenlibvaluesets()
        self.senotypetree = self._getsenotypejtree()
        # print(json.dumps(self.senotypetree, indent=2))

    def getsenlibvalueset(self, predicate: str) -> pd.DataFrame:
        """
        Getter-like method.
        Obtain the valueset associated with an assertion predicate.
        :param dfvaluesets: valueset dataframe
        :param predicate: assertion predicate. Can be either an IRI or a term.
        """

        df = self.senlibvaluesets

        # Check whether the predicate corresponds to an IRI.
        dfassertion = df[df['predicate_IRI'] == predicate]
        if len(dfassertion) == 0:
            # Check whether the predicate corresponds to a term.
            dfassertion = df[df['predicate_term'] == predicate]

        return dfassertion

    def getsenlibterm(self, predicate: str, code: str) -> str:
        """
        Returns the term from a valueset for a code.
        :param predicate: assertion predicate for the valueset.
        :param code: code key
        """

        valueset = self.getsenlibvalueset(predicate=predicate)
        matched = valueset.loc[valueset['valueset_code'] == code, 'valueset_term']
        term = matched.iloc[0] if not matched.empty else None

        return term