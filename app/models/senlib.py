"""
Class for working with Senotype submission JSON files in the senlib repository.
"""
import logging
from models.restapi import RestAPI

# Configure consistent logging. This is done at the beginning of each module instead of with a superclass of
# logger to avoid the need to overload function calls to logger.
logging.basicConfig(format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
                    level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


class SenLib:

    def _getsenliblist(self) -> list:
        """
        Obtains list of files in the senlib repo.
        """
        api = RestAPI()
        return api.getresponsejson(url=self.senliburl)

    def _getsenlibjsonids(self) -> list:
        """
        Obtain all senlib jsons from repo.
        :return: list of senlib JSON IDs
        """

        listfiles = self._getsenliblist()
        listids = []
        for f in listfiles:
            listids.append(f.get('name'))

        return listids

    def __init__(self, url: str):

        # Obtain list of senlib JSONs.
        self.senliburl = url
        self.senlibjsonids = self._getsenlibjsonids()
