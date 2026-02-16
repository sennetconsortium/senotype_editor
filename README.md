# Senotype Editor

The Senotype Editor allows a user to manage the individual Senotype Library submission files in the [senlib](https://github.com/sennetconsortium/senlib) database.

The Senotype Editor is a Single Page Application based in Python Flask, Jinja2, jquery, and JavaScript.

# Help files
[User documentation files](https://github.com/sennetconsortium/senotype_editor/blob/main/docs/HELP.md) are located in the _docs_ folder of this repo.

GitHub Pages has been configured to display this documentation in a link in the main navbar of the Editor. 
The Pages link is https://sennetconsortium.github.io/senotype_editor/.

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

# Docker deployment
Run `docker compose up --build` in the _docker_ directory.

The Docker configuration expects the **app.cfg** file to be in the directory _~/senotype-editor_.

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

## Application flow
The Senotype Editor is essentially a Single Page Application: aside from a login page to manage initial Globus login, functions are 
managed in the Edit page.

### Login
The application index page (/route) invokes Globus login, authentication, and authorization (routes under _globus_auth_.)

A user can only use the Senotype Editor if their account has appropriate authorization. Initially, authorization 
depends on membership in a particular Globus user group.

If the user is authorized, the application routes to the Edit page.

### Edit
#### Initial load
After a successful Globus login, the Edit page:
1. reads configuration information (via an AppConfig class)
2. connects to an instance of the Senlib database (via the SenLib and SenLibMySql classes)
3. populates the Senotype Navigator treeview
4. builds the set of modal windows that will be used to select data to add to a senotype

Building the modal search windows involves Jinja templates (including _search_modal_macro.html_ 
and _valueset_modal_macro.html_).

#### Senotype Navigator
The Senotype Navigator is a jstree control that is populated from a JSON built from data obtained
from the Senlib database. Navigator functionality requires interaction between Javascripts
(such as _senotype-treeview.js_), WTForms, and HTML.

#### Initiation of new senotype
When the user selects the **new** node in the Navigator, the Edit form reloads and:
1. uses the uuid-api to create a SenNet ID for a new senotype
2. enables inputs for editing
3. enables the "Create" button

#### Selection of existing senotype
When the user selects a node in the Senotype Navigator that corresponds to an existing senotype, the Edit form reloads and:
1. fetches the senotype's data from Senlib
2. populates inputs with existing data
3. enables the "Update" button

#### Population of inputs
Because most of the assertions of a senotype are categorical, the majority
of inputs on the Edit form are lists. 

Each element of a list corresponds to the 
object of an assertion between the element and the senotype. 
Each element of a list may contain:
* the object's code in a vocabulary
* a link to a detail page for the object, if the object's code is from an external source
* an "add" button
* a "remove" button

Population of data for an element of a list involves interaction between
WTForms, Jinja templates, and Javascript.

#### Adding categorical data

Adding a categorical value to a list involves the display of a modal selection window.
A selection window is populated by an interaction between Jinja macros (including
_search_modal_macro.html_ and _valueset_modal_macro.html_) and Javascripts
(including _valueset-modal.js_, _external-list-modal.js_, _regmarker-csv.js_, 
_regmaker-modal.js_, _marker-csv.js_, and _marker-modal.js_.). 

Search buttons in selection forms for external assertions execute routes that call REST APIs (e.g., in the _/ontology_ and _/origin_ paths).

If a user selects a value from a list generated by a search modal, the associated Javascript adds an element to the 
corresponding list in the Edit form.

#### Creating/Updating a senotype

A button below the Edit form has a label of either "Create" or "Update", depending 
on whether the senotype is new or existing. 

The response to clicking the button depends on the type of request.
* If "Create", the application will
  * validate inputs, including
    * verifying that required inputs are present
    * verifying that ranges for context assertions are correct (e.g. that the upper bound is greater than the lower bound)
  * insert a new senotype record into SenLib

* If "Update", the application will
  * validate inputs
  * update the existing senotype record in SenLib
  * if there was a validation error, cache input data in a session cookie

Both options reload the Edit page (via the _/edit_ route) and re-select the senotype node in the Navigator.

When reloaded from a creation or update, the Edit page checks for validation error information stored by the loading action.
If there are validation errors, the page populates input data from the session cookie; otherwise, the page
populates inputs from data obtained from SenLib.

# Configuration
The application uses **app.cfg** to obtain:
- consortium options (SenNet)
- uuid base URL (e.g., development or production)
- Globus client keys and secrets for SenNet
- base URLs for external APIs and detail pages

The configuration file must be kept separate from the application in either of its possible deployments:
1. In a "bare-metal" deployment, in which the application is run from within a clone of the GitHub repository, the configuration file must be located in a subdirectory of the user root (~) named _senotype-editor_.
2. In a "containerized" deployment, in which the application is executed from within a Docker container, the configuration file must not be in the container. The application looks for the app.cfg file in the /usr/src/app/instance
folder, which will be bound to a volume on the host machine by the Docker Compose file.

