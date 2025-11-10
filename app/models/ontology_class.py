"""
Class for working with the hs-ontology-api
"""
from flask import make_response
from models.requestretry import RequestRetry
from models.appconfig import AppConfig


class OntologyAPI:

    def __init__(self):
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
        print(url)
        response = api.getresponse(url=url, format='json')
        print(response)
        if type(response) is dict:
            if response.get('message') is not None:
                return make_response(f'no {target} found', 404)
            else:
                return response
        else:
            return response
