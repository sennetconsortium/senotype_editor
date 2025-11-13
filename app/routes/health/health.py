from flask import Blueprint

health_blueprint = Blueprint('health', __name__)


@health_blueprint.route('/health', methods=['GET'])
def get_health():
    """
    Used for health checks of the Senotype Editor application.

    """
    return "OK", 200
