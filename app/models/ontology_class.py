"""
Class for working with the hs-ontology-api
"""
from flask import make_response
from models.requestretry import RequestRetry
from models.appconfig import AppConfig


class OntologyAPI:

    def __init__(self):
        api = RequestRetry()
        cfg = AppConfig()
        self.urlbase = f"{cfg.getfield(key='UBKG_BASE_URL')}"

    def get_ontology_api_response(self, endpoint: str, target: str):
        """
        Returns the response of an endpoint of the hs-ontology-api.
        :param endpoint: portion of the endpoint to append to the urlbase.
        :param target: description of the endpoint's entity--e.g., genes
        """
        api = RequestRetry()
        url = f"{self.urlbase}/{endpoint}"
        response = api.getresponse(url=url, format='json')
        if type(response) is dict:
            return make_response(f'no {target} found', 400)
        else:
            return response
