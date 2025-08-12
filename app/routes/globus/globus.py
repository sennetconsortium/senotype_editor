"""
Index route that:
1. obtains Globus environment and donor id from a WTForm (GlobusForm)
2. authenticates to Globus
"""

from flask import Blueprint, request, render_template, redirect, session

globus_blueprint = Blueprint('globus', __name__, url_prefix='/')


@globus_blueprint.route('', methods=['GET', 'POST'])
def globus():

    #form = GlobusForm(request.form)

    # Clear messages.
    if 'flashes' in session:
        session['flashes'].clear()

    # if request.method == 'POST' and form.validate():
    # Pass the Globus environment to which to authenticate.
    session['consortium'] = 'CONTEXT_SENNET'
    # Authenticate to Globus via the login route.
    # If login is successful, Globus will redirect to the edit page.
    return redirect(f'/login')

    return render_template('edit.html')
