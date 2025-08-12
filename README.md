# Senotype Editor

The Senotype Editor allows a user to manage the individual Senotype Library submission files in the [senlib](https://github.com/sennetconsortium/senlib) repository.

# User Interface
The Senotype Editor's User Interface is based on:

| tool                                                                            | purpose                                                      |
|---------------------------------------------------------------------------------|--------------------------------------------------------------|
| Python                                                                          | application function                                         |
| [Flask](https://flask.palletsprojects.com/en/3.0.x/)                            | Python web framework                                         |
| [Flask Blueprints](https://flask.palletsprojects.com/en/3.0.x/blueprints/)      | modular Flask applications                                   |
| [WTForms](https://wtforms.readthedocs.io/en/2.3.x/forms/)                       | forms in Flask applications                                  |
| [Jinja](https://jinja.palletsprojects.com/en/3.1.x/)                            | Web page templating                                          |
| Javascript                                                                      | Event handling and UI features (including a spinner control) |
| [Bootstrap](https://getbootstrap.com/)                                          | UI toolkit                                                   ||
| [SenNet entity-api](https://smart-api.info/ui/7d838c9dee0caa2f8fe57173282c5812) | Reads source metadata in SenNet provenance                   |

## Configuration
The application uses **app.cfg** to obtain:
- consortium options (SenNet)
- entity-api environment (e.g., development or production)
- Globus client keys and secrets for HuBMAP and SenNet

The configuration file must be kept separate from the application in either of its possible deployments:
1. In a "bare-metal" deployment, in which the application is run from within a clone of the GitHub repository, the configuration file must not be in the repo. 
2. In a "containerized" deployment, in which the application is executed from within a Docker container, the configuration file must not be in the container. The application looks for the app.cfg file in the /usr/src/app/instance
folder, which is bound to a volume on the host machine.

