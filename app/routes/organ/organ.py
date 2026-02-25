"""
The dataset routes allow the Edit page to call the SenNet Data Portal's organ page.

"""
from flask import redirect, Blueprint

from models.ontology_class import OntologyAPI
from models.appconfig import AppConfig

organ_blueprint = Blueprint('organs', __name__, url_prefix='/organs')


@organ_blueprint.route('/home', methods=['GET'])
def get_organ_home():
    """
    Loads the SenNet Data Portal Organs page.
    """

    cfg = AppConfig()
    url = f"{cfg.getfield(key='DATA_PORTAL_BASE_URL')}/organs"
    return redirect(url)


@organ_blueprint.route('/<uberon_id>', methods=['GET'])
def get_organ(uberon_id):
    """
    Obtains a search term for an organ in the SenNet Data Portal organs page.
    :param uberon_id: UBERON code for the organ.

    """

    ontapi = OntologyAPI()
    endpoint = f'organs?application_context=sennet'
    organs = ontapi.get_ontology_api_response(endpoint=endpoint, target='organs')

    # The organs page uses as search term the term from the UBKG organ endpoint.
    # For organs with laterality (e.g., left lung), the search term corresponds to that of the
    # organ category.

    for organ in organs:
        if organ.get('organ_uberon') == uberon_id:
            category = organ.get('category')
            if category is None:
                term = organ.get('term')
            else:
                term = category.get('term')
            term = term.lower().replace(' ', '-')

            cfg = AppConfig()
            organ_url = f"{cfg.getfield(key='DATA_PORTAL_BASE_URL')}/organs"
            url = f"{organ_url}/{term}"
            return redirect(url)
