"""
Senotype edit route.
Works with editform.py.

"""

from flask import Blueprint, request, render_template, flash, session, abort
from wtforms import SelectField, Field

edit_blueprint = Blueprint('edit', __name__, url_prefix='/edit')


@edit_blueprint.route('', methods=['POST', 'GET'])
def edit():

    print('edit!')
    return render_template('edit.html')










