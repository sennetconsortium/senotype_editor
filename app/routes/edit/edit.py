"""
Senotype edit route.
Works with editform.py.

"""

from flask import Blueprint, request, render_template, flash, session, abort
from wtforms import SelectField, Field

# WTForms
from models.editform import EditForm

edit_blueprint = Blueprint('edit', __name__, url_prefix='/edit')


@edit_blueprint.route('', methods=['POST', 'GET'])
def edit():
    # Load the edit form and the edit page.
    form = EditForm(request.form)
    return render_template('edit.html', form=form)










