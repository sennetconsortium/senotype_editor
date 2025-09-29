# Senotype Editor

The Senotype Editor allows a user to manage the individual Senotype Library submission files in the [senlib](https://github.com/sennetconsortium/senlib) database.

The Senotype Editor is a Single Page Application based in Python Flask, Jinja2, jquery, and JavaScript.

# Help files
User documentation files are located in the Help subdirectory of this repo.

# Local Development
To run the Senotype Editor locally,
1. Clone this repo.
2. Establish a python virtual environment.
3. Install the packages in *requirements.txt*.
4. Set up the *app.cfg* file:
   * Create a subdirectory of the user root (corresponding to ~) named *senotype_editor*.
   * Copy the *app.cfg.example* file (in the */app/instance* path) to the *senotype_editor* directory. 
   * Rename *app.cfg.example* *app.cfg*.
   * Edit *app.cfg*, providing values for 
     * connection parameters for the Senlib database, which is a MySQL instance running in SenNet's AWS environment
     * The Globus secret keys for the SenNet consortium
5. Run *app.py* in Python.
6. Open  http://127.0.0.1:5000, which will load the Senotype Editor Edit page.

The User documentation will explain the functions of the Senotype Editor.

# Application Architecture
The Senotype Editor's User Interface is based on:

| tool                                                                            | purpose                                |
|---------------------------------------------------------------------------------|----------------------------------------|
| Python                                                                          | application function, business logic   |
| [Flask](https://flask.palletsprojects.com/en/3.0.x/)                            | Python web framework                   |
| [Flask Blueprints](https://flask.palletsprojects.com/en/3.0.x/blueprints/)      | modular Flask applications             |
| [WTForms](https://wtforms.readthedocs.io/en/2.3.x/forms/)                       | forms in Flask applications            |
| [Jinja](https://jinja.palletsprojects.com/en/3.1.x/)                            | Web page templating linked to WTForms  |
| Javascript                                                                      | Event handling and UI features         |
| [jquery](https://jquery.com/)                                                   | calling API from JavaScript            |
| [jstree](https://www.jstree.com/)                                               | implements the Senotype treeview       |
| [Bootstrap](https://getbootstrap.com/)                                          | UI toolkit                             |
| [SenNet entity-api](https://smart-api.info/ui/7d838c9dee0caa2f8fe57173282c5812) | Obtains information on SenNet datasets |
| [uuid-api](https://github.com/x-atlas-consortia/uuid-api)                       | Creates SenNet IDs                     |


# Configuration
The application uses **app.cfg** to obtain:
- consortium options (SenNet)
- uuid base URL (e.g., development or production)
- Globus client keys and secrets for SenNet

The configuration file must be kept separate from the application in either of its possible deployments:
1. In a "bare-metal" deployment, in which the application is run from within a clone of the GitHub repository, the configuration file must be located in a subdirectory of the user root (~) named _senotype-editor_.
2. In a "containerized" deployment, in which the application is executed from within a Docker container, the configuration file must not be in the container. The application looks for the app.cfg file in the /usr/src/app/instance
folder, which will be bound to a volume on the host machine by the Docker Compose file.

