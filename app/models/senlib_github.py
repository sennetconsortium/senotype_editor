"""
Class for working with senlib as GitHub repo.

"""

import pandas as pd
from io import StringIO
import json

from models.appconfig import AppConfig
from models.requestretry import RequestRetry

import logging
# Configure consistent logging. This is done at the beginning of each module instead of with a superclass of
# logger to avoid the need to overload function calls to logger.
logging.basicConfig(format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
                    level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


class SenLibGitHub():

    def _getsenlibrepolist(self) -> list:
        """
        Obtains list of files in the senlib repo.
        """
        return self.request.getresponse(url=self.senlib_url,
                                        format='json',
                                        headers=self.github_header)

    def _getsenotypeids(self) -> list:
        """
        Obtains the ids of all Senotype submissions in the senlib repo.
        :return: list of Senotype ids
        """

        listdir = self._getsenlibrepolist()
        listids = []

        # The latest version of a Senotype will not have a successor.
        for entry in listdir:
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

    def getsenlibjson(self, id: str) -> dict:
        """
        Get a single senotype JSON.
        :param id: id of the senotype, corresponding to the file name in the data
                   source.
        :return: the senotype json
        """
        url = f'{self.json_url}/{id}.json'
        return self.request.getresponse(url=url, format='json')

    def _getsenlibvaluesets(self) -> pd.DataFrame:
        """
        Get the Senotype Editor valueset from the senlib repo as a Pandas DataFrame.
        :return:
        """

        # Get the text stream from GitHub.
        stream=self.request.getresponse(url=self.valueset_url, format='csv')
        # Convert to a string.
        csv_data = StringIO(stream)
        # Read into Pandas.
        return pd.read_csv(csv_data)

    def __init__(self, cfg: AppConfig):
        """
        :param cfg: AppConfig, representing the app.cfg file.
        """

        # For calling the GitHub API.
        self.request = RequestRetry()

        # Get the URLs to the senlib repo.
        # Base URL for the repo
        self.senlib_url = cfg.getfield(key='SENOTYPE_URL')
        # URL to the Senotype Editor valueset CSV, stored in the senlib repo
        self.valueset_url = cfg.getfield(key='VALUESET_URL')
        # URL to the folder for Senotype Submissions in the senlib repo
        self.json_url = cfg.getfield(key='JSON_URL')
        # Github personal access token for authorized calls
        github_token = cfg.getfield(key='GITHUB_TOKEN')
        self.github_header = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
            }

        # Get IDs for all senlib JSONs.
        self.senlibjsonids = self._getsenotypeids()

        # Get the application valuesets.
        self.senlibvaluesets = self._getsenlibvaluesets()


