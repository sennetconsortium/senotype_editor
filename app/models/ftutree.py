"""
FTUTree
Class that builds the data structure to support a jstree based on the
2D FTU CSV.
"""
import requests
import logging
import pandas as pd
from io import StringIO


class FTUTree:
    def _iri_value(self, iri: str):
        """
        Parses the code from an IRI.

        """
        if pd.isnull(iri):
            return ""
        return iri.split("/")[-1]

    def _readftucsv(self) -> pd.DataFrame:
        """
        Reads the 2D FTU CSV into a DataFrame.
        """

        # The URL is for a direct download, so mimic a browser.
        url = "https://apps.humanatlas.io/api/grlc/hra/2d-ftu-parts.csv"
        headers = {
            "User-Agent": "Mozilla/5.0",  # Mimic browser
            "Accept": "text/csv",
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()  # will raise for 500/404

        csv_data = StringIO(response.text)
        df = pd.read_csv(csv_data)

        return df

    def _getftujtree(self) -> list[dict]:
        """
        Builds the source for the FTU treeview.
        """

        # Get the 2D FTU data.
        df = self._readftucsv()

        # Loop through the FTU DataFrame.

        organs = {}

        for _, row in df.iterrows():
            organ_label = row['organ_label']
            organ_iri = row['organ_iri']
            organ_val = self._iri_value(organ_iri)

            ftu_label = row['ftu_label']
            ftu_iri = row['ftu_iri']
            ftu_val = self._iri_value(ftu_iri)

            ftu_part_label = row['ftu_part_label']
            ftu_part_iri = row['ftu_part_iri']
            ftu_part_val = self._iri_value(ftu_part_iri)

            # Organ node
            if organ_val not in organs:
                organs[organ_val] = {
                    "id": f"organ_{organ_val}",
                    "text": organ_label,
                    "data": {"value": organ_val, "iri": organ_iri},
                    "children": {}
                }
            organ_node = organs[organ_val]

            # FTU node (under organ)
            if ftu_val not in organ_node["children"]:
                organ_node["children"][ftu_val] = {
                    "id": f"{organ_node['id']}_ftu_{ftu_val}",
                    "text": ftu_label,
                    "data": {"value": ftu_val, "iri": ftu_iri},
                    "children": []
                }
            ftu_node = organ_node["children"][ftu_val]

            # FTU Part node (under FTU).

            ftu_node["children"].append({
                "id": f"{ftu_node['id']}_part_{ftu_part_val}",
                "text": ftu_part_label,
                "data": {"value": ftu_part_val, "iri": ftu_part_iri},
            })

        # Convert children dicts to lists for jsTree
        jstree = []
        for organ in organs.values():
            organ['children'] = list(organ['children'].values())
            jstree.append(organ)

        return jstree

    def __init__(self):

        self.ftutree = self._getftujtree()