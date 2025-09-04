"""
Class for working with Senotype submission JSON files in the senlib repository.
"""
import logging
import pandas as pd
from io import StringIO
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

    def _getlatestsenotypeids(self) -> list:
        """
        Obtains the latest versions of all Senotype submissions in the senlib repo.
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
            if successor is None:
                id = senotypeid
                name = senotype.get('name', '')
                if name != '':
                    if len(name) >= 50:
                        name = f'{name[0:47]}...'

                listids.append(f'{id} ({name})')

        return listids

    def getsenlibjson(self, id: str) -> dict:
        """
        Get a Senotype submission JSON.
        :param id: id of the senotype, corresponding to the file name.
        :return:
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
        self.senlibjsonids = self._getlatestsenotypeids()
        self.senlibvaluesets = self._getsenlibvaluesets()

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
