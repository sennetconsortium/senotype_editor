"""
Class that executes REST API calls to fetch information
from external APIs for encoded SenLib entities.
"""

import logging
from flask import request, session, abort

# For external API requests
from models.requestretry import RequestRetry

# Application configuration object
from models.appconfig import AppConfig

# Configure consistent logging. This is done at the beginning of each module instead of with a superclass of
# logger to avoid the need to overload function calls to logger.
logging.basicConfig(format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
                    level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

class SenLibAPI:

    def __init__(self):

        self.api = RequestRetry()
        self.cfg = AppConfig()

    def getubkgstatus(self) -> str:

        """
        Check the status of the UBKG API.
        """
        statusurl = self.cfg.getfield('UBKG_BASE_URL')

        try:
            status = self.api.getresponse(url=statusurl)
            if 'Hello!' in status:
                return 'OK'
            else:
                return 'NOT OK'

        except ConnectionError as e:
            abort(500, description=f'Error connecting to the UBKG API: {e}')

    def getdatacitestatus(self) -> str:

        # Checks the status of DataCite.
        urlheartbeat = self.cfg.getfield('DATACITE_HEARTBEAT_URL')

        status = self.api.getresponse(url=urlheartbeat)
        return status

    def getcitationtitle(self, pmid: str) -> str:
        """
        Calls the NCBI EUtils API (via the citation/search route) to obtain the title for the PMID.

        """
        logging.info('Getting citation data from NCBI EUtils')
        base_url = f"{request.host_url.rstrip('/')}/citation/search/id/"
        url = f'{base_url}{pmid}'

        citation = self.api.getresponse(url=url, format='json')
        result = citation.get('result')
        title = 'unknown'
        if result is not None:
            entry = result.get(pmid)
            if entry is not None:
                title = entry.get('title', '')
        return title

    def getorigindescription(self, code: str) -> str:
        """
        Calls the SciCrunch API to obtain the title for a RRID.
        :param: code - the RRID code
        """

        logger.info('Getting origin information from SciCrunch Resolver')
        base_url = self.cfg.getfield(key='SCICRUNCH_BASE_URL')

        # IDs for Antibodies and cells have higher resolution (vendor)
        # than RRID, using the dash as delimiter. However, the
        # search URL that returns JSON only has resolution at the
        # RRID level. Strip higher-resolution identifiers.
        searchcode = code
        if '-' in code:
            searchcode = code.split('-')[0]
        url = f'{base_url}{searchcode}.json'

        origin = self.api.getresponse(url=url, format='json')
        description = 'unknown'
        if origin is not None:
            hits = origin.get('hits')
            if hits is not None:
                if len(hits.get('hits')) > 0:
                    description = hits.get('hits')[0].get('_source').get('item').get('name', '')

        return description

    def getdatasettitle(self, snid:str) -> str:

        """
        Calls the entity API to obtain the title for a SenNet dataset.
        :param snid: SenNet dataset identifier.
        """

        logger.info('Getting dataset information from SenNet entity-api')

        token = session['groups_token']
        headers = {"Authorization": f'Bearer {token}'}
        base_url = self.cfg.getfield(key='ENTITY_BASE_URL')
        url = f'{base_url}{snid}'
        dataset = self.api.getresponse(url=url, format='json', headers=headers)
        title = dataset.get('title', '')
        if title is None or title.strip() == '':
            title = 'unknown'

        return title

    def getcelltypeterm(self, code: str) -> str:
        """
        Calls the UBKG API to obtain descriptions for cell types.
        :param code: cell type code
        """

        logger.info('Getting celltype information from the ontology API')

        base_url = f"{request.host_url.rstrip('/')}/ontology/celltypes/"
        url = f'{base_url}{code}'
        celltype = self.api.getresponse(url=url, format='json')

        name = 'unknown'
        # celltypes returns a list of JSON objects
        if len(celltype) > 0:
            name = celltype[0].get('cell_type').get('name', '')

        return name

    def getlocationterm(self, code: str) -> str:
        """
        Calls the UBKG API to obtain descriptions for an organ.
        :param code: organ code
        """

        logger.info('Getting organ information from the ontology API')
        base_url = f"{request.host_url.rstrip('/')}/ontology/organs"

        url = f'{base_url}/{code}/code'
        organs = self.api.getresponse(url=url, format='json')

        # organs returns a list of JSON objects
        term = 'unknown'
        if len(organs) > 0:
            term = organs[0].get('term')

        return term

    def getdiagnosisterm(self, code: str) -> str:
        """
        Calls the UBKG API to obtain descriptions for diagnoses.
        :param code: diagnose code
        """
        logger.info('Getting diagnosis information from the ontology API')
        base_url = f"{request.host_url.rstrip('/')}/ontology/diagnoses/"

        url = f'{base_url}{code}/code'
        diagnoses = self.api.getresponse(url=url, format='json')

        # diagnoses returns a list of JSON objects
        term = 'unknown'
        if len(diagnoses) > 0:
            term = diagnoses[0].get('term')
        return term

    def getmarkerdescription(self, code: str) -> str:
        """
        Calls the UBKG API to obtain the description for specified markers.
        :param: code - marker code
        """

        logger.info('Getting marker information from the ontology API')
        base_url = self.cfg.getfield('UBKG_BASE_URL')

        markerid = code.split(':')[1]
        markertype = code.split(':')[0]
        if markertype == 'HGNC':
            marker = 'genes'
        else:
            marker = 'proteins'

        url = f'{base_url}/{marker}/{markerid}'

        resp = self.api.getresponse(url=url, format='json')
        # Defensive: check if resp is a list and not empty
        term = 'unknown'

        if not resp or not isinstance(resp, list) or not resp[0]:
            term = 'unknown'
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
        return term

    def getdoidescription(self, doi_url: str) -> str:
        """
        Calls the DataCite API to obtain the title for a DOI.
        :param doi_url: DOI url
        """

        datacite_base = self.cfg.getfield(key='DATACITE_DOI_BASE_URL')
        doi = doi_url.split(datacite_base)[1]
        url_base = self.cfg.getfield(key='DATACITE_API_BASE_URL')
        url = f'{url_base}{doi}'

        logger.info(f'Getting DataCite information for {doi}')

        response = self.api.getresponse(url=url, format='json')
        if response is None:
            urlheartbeat = self.cfg.getfield(key='DATACITE_HEARTBEAT_URL')
            responseheartbeat = self.api.getresponse(url=urlheartbeat)
            if responseheartbeat == 'OK':
                title = 'unknown title'
            else:
                title = 'invalid response from DataCite API'
        else:
            title = response.get('data').get('attributes').get('titles')[0].get('title', '')

        return title

