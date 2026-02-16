"""
Index route that authenticates to Globus to allow calls to SenNet APIs:
- entity-api
- uuid-api
"""

from flask import Blueprint, request, redirect, session

globus_blueprint = Blueprint('globus', __name__, url_prefix='/')


@globus_blueprint.route('', methods=['GET'])
def globus():

    # Clear messages.
    if 'flashes' in session:
        session['flashes'].clear()

    if request.method == 'GET':
        # Pass the Globus environment to which to authenticate.
        session['consortium'] = 'CONTEXT_SENNET'
        # Authenticate to Globus via the login route.
        # If login is successful, Globus will redirect to the edit page.
        print('Logging into Globus...')
        return redirect(f'/auth')
