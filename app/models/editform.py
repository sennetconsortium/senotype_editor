"""
Form used to manage Senotype submisstion JSONs.
"""


from wtforms import (Form, StringField, SelectField, DecimalField, validators, ValidationError,
                     TextAreaField, SubmitField)

# Helper classes
# Represents the app.cfg file
from models.appconfig import AppConfig
from models.senlib import SenLib


def validate_age(form, field):
    """
    Custom validator. Checks that age is at least 1 month.

    :param form: the Edit form
    :param field: the age field
    :return: Nothing or raises ValidationError
    """

    ageunit = form.ageunit.data
    age = field.data
    if stringisintegerorfloat(age) == "not a number":
        raise ValidationError('Age must be a number.')
    agenum = float(age)
    if age is None:
        age = 0
    if agenum > 89 and ageunit == 'C0001779':  # UMLS CUI for age in years
        if agenum != 90:
            raise ValidationError('All ages over 89 years must be set to 90 years.')


def validate_number(form, field):
    """
    Custom validator for StringFields that collect numeric data.
    :param form: the Edit form
    :param field: the field to check
    :return: Nothing or raises ValidationError
    """

    valuetotest = field.data
    test = stringisintegerorfloat(valuetotest)

    if test == "not a number":
        raise ValidationError(f'{field.name} must be a number.')


def validate_integer(form, field):
    """
    Custom validator for StringFields that collect integer data.
    :param form: the Edit form
    :param field: the field to check
    :return: Nothing or raises ValidationError
    """

    valuetotest = field.data
    test = stringisintegerorfloat(valuetotest)

    if test != "integer":
        raise ValidationError(f'{field.name} must be an integer.')

def validate_selectfield_default(form, field):
    """
    Custom validator that checks whether the value specified in a SelectField's data property is in
    the set of available values.
    Handles the case of where there is a mismatch between an existing metadata value for a donor and the
    corresponding SelectField in the Edit form.

    :return: nothing or ValidationError
    """
    found = False
    for c in field.choices:
        if field.data == c[0]:
            found = True
    if not found:
        msg = f"Selected concept '{field.data}` not in valueset."
        raise ValidationError(msg)


def validate_required_selectfield(form, field):
    """
    Custom validator that verifies that the value specified in a SelectField deemed required (e.g., Source)
    is other than the prompt.

    """
    if field.data == 'PROMPT':
        msg = f'Required'
        raise ValidationError(msg)


# ----------------------
# MAIN FORM


class EditForm(Form):

    # POPULATE FORM FIELDS.

    # Read the app.cfg file outside the Flask application context.
    cfg = AppConfig()

    # Existing Senotype submissions.

    # Get the URL to the senlib repo.
    github_url = cfg.getfield(key='GITHUB_URL')
    senlib = SenLib(url=github_url)
    choices = ['(new)'] + senlib.senlibjsonids
    senotypeid = SelectField('Senotype ID', choices=choices)

