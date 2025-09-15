# Senotype Editor
import os
import logging
from pathlib import Path
from flask import Flask, render_template
import json

from models.appconfig import AppConfig

# Register Blueprints
from routes.auth.auth import login_blueprint
from routes.globus.globus import globus_blueprint
from routes.edit.edit import edit_blueprint
from routes.valueset.valueset import valueset_blueprint
from routes.ontology.ontology import ontology_blueprint
from routes.update.update import update_blueprint
from routes.dataset.dataset import dataset_blueprint


def to_pretty_json(value):
    # Custom pretty printer of JSON, used for rendering JSON in <pre> elements.
    return json.dumps(value, sort_keys=True,
                      indent=4, separators=(',', ': '))


# Configure consistent logging. This is done at the beginning of each module instead of with a superclass of
# logger to avoid the need to overload function calls to logger.
logging.basicConfig(format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
                    level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


class SenotypeUI:

    def __init__(self, config: str, package_base_dir: Path):
        self.app = Flask(__name__,
                         instance_path=os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance'),
                         instance_relative_config=True)

        self.app.package_base_dir = package_base_dir

        # Set secret key for app.
        self.config = config
        self.app.config.from_pyfile(self.config)
        self.app.secret_key = self.app.config['KEY']

        logger.info(f"package_base_dir: {package_base_dir}")

        # Register route Blueprints.
        self.app.register_blueprint(login_blueprint)
        self.app.register_blueprint(globus_blueprint)
        self.app.register_blueprint(edit_blueprint)
        self.app.register_blueprint(valueset_blueprint)
        self.app.register_blueprint(ontology_blueprint)
        self.app.register_blueprint(update_blueprint)
        self.app.register_blueprint(dataset_blueprint)

        # Register the custom JSON pretty print filter.
        self.app.jinja_env.filters['tojson_pretty'] = to_pretty_json

        # The consortium authentication token is stored in a session cookie.
        # Set cookie expiration:
        # Set the session lifetime to 30 minutes (in seconds).
        self.app.config['PERMANENT_SESSION_LIFETIME'] = 300 * 60

        # Custom 400 error handler.
        @self.app.errorhandler(400)
        def badrequest(error):
            return render_template('400.html', error=error), 400

            # Custom 400 error handler.

        # Custom 401 error handler.
        @self.app.errorhandler(401)
        def unauthorized(error):
            return render_template('401.html'), 401

        @self.app.errorhandler(403)
        def forbidden(error):
            return render_template('403.html', error=error), 403

        # Custom 404 error handler.
        @self.app.errorhandler(404)
        def notfound(error):
            return render_template('404.html', error=error), 404

        # Custom 404 error handler.
        @self.app.errorhandler(500)
        def servererror(error):
            return render_template('500.html', error=error), 500


# ###################################################################################################
# For local development/testing
# ###################################################################################################


if __name__ == "__main__":

    # Obtain the path to the configuration file.
    cfg = AppConfig()

    try:
        donor_app = SenotypeUI(cfg.file, Path(__file__).absolute().parent.parent.parent).app
        donor_app.run(host='0.0.0.0', port='5000')  # flask port
    except Exception as e:
        print(str(e))
        logger.error(e, exc_info=True)
        print('Error during startup of debug server. Check the log file for further information.')
