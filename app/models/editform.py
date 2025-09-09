"""
Form used to manage Senotype submisstion JSONs.
"""


from wtforms import (Form, SelectField, validators, ValidationError,
                     TextAreaField, FieldList, StringField, FormField, RadioField)
from wtforms.validators import Email

# Helper classes
from models.appconfig import AppConfig
from models.senlib import SenLib
from models.stringnumber import stringisintegerorfloat



def validate_age(form, field):
    """
    Custom validator for age.

    Assumes that age unit is years.

    :param field: the age field
    :return: Nothing or raises ValidationError
    """

    age = field.data
    if age.strip() == '':
        return

    if stringisintegerorfloat(age) == 'not a number':
        raise ValidationError('Age must be a number.')

    agenum = float(age)

    if age is None:
        age = 0
    if agenum < 0:
        raise ValidationError('Age must be positive.')
    if agenum > 89:
        raise ValidationError('Ages over 89 years must be set to 90 years.')


def validate_number(field):
    """
    Custom validator for StringFields that collect numeric data.
    :param field: the field to check
    :return: Nothing or raises ValidationError
    """

    valuetotest = field.data
    test = stringisintegerorfloat(valuetotest)

    if test == "not a number":
        raise ValidationError(f'{field.name} must be a number.')


def validate_integer(field):
    """
    Custom validator for StringFields that collect integer data.
    :param field: the field to check
    :return: Nothing or raises ValidationError
    """

    valuetotest = field.data
    test = stringisintegerorfloat(valuetotest)

    if test != "integer":
        raise ValidationError(f'{field.name} must be an integer.')


# ----------------------
# MAIN FORM
def getchoices(sl: SenLib, predicate: str) -> list[tuple]:
    """
    Return a list of tuples for a valueset.
    :param sl: the SenLib interface
    :param predicate: assertion predicate. Can be either an IRI or a term.
    """
    # Get the DataFrame of valueset information corresponding to an assetion predicate.
    dfchoices = sl.getsenlibvalueset(predicate=predicate)

    # Buiild a list of tuples from the relevant columns of the DataFrame.
    choices = list(zip(dfchoices['valueset_code'], dfchoices['valueset_term']))

    # Add 'select' as an option. Must be a tuple for correct display in the form.
    choices = [("select", "select")] + choices
    return choices


class RegMarkerEntryForm(Form):

    # The regulating marker data is stored in lists in two hidden inputs:
    # - the marker code
    # - regulating action

    marker = StringField('Regulating Marker')
    action = StringField('Regulating Action')


class EditForm(Form):

    # Set up the Senlib interface to obtain valueset information.

    # Read the app.cfg file outside the Flask application context.
    cfg = AppConfig()
    # Get the URLs to the senlib repo.
    senlib_url = cfg.getfield(key='SENOTYPE_URL')
    valueset_url = cfg.getfield(key='VALUESET_URL')
    json_url = cfg.getfield(key='JSON_URL')

    # Senlib interface
    senlib = SenLib(senlib_url, valueset_url, json_url)

    # SET DEFAULTS

    # Senotype
    senotypeid = StringField('ID')
    senotypename = StringField('Senotype Name', validators=[validators.InputRequired()])
    senotypedescription = TextAreaField('Senotype Description', validators=[validators.InputRequired()])
    doi = StringField('DOI')

    # Provenance and version
    provenance = FieldList(StringField('Provenance ID'), min_entries=0)

    # Submitter
    submitterfirst = StringField('First Name', validators=[validators.InputRequired()])
    submitterlast = StringField('Last Name', validators=[validators.InputRequired()])
    submitteremail = StringField('email', validators=[validators.InputRequired(), Email(message='Invalid email address.')])

    # Simple assertions.
    # These lists require custom validators because they will be updated via Javascript.
    taxon = FieldList(StringField('Taxon'), min_entries=0, label='Taxon')
    location = FieldList(StringField('Location'), min_entries=0)
    celltype = FieldList(StringField('Cell type'), min_entries=0)
    hallmark = FieldList(StringField('Hallmark'), min_entries=0)
    observable = FieldList(StringField('Molecular Observable'), min_entries=0)
    inducer = FieldList(StringField('Inducer'), min_entries=0)
    assay = FieldList(StringField('Assay'), min_entries=0)

    # Context assertions
    agevalue = StringField('Value', validators=[validate_age])
    agelowerbound = StringField('Lowerbound', validators=[validate_age])
    ageupperbound = StringField('Upperbound', validators=[validate_age])
    ageunit = StringField('Unit')


    # External assertions
    # Citations
    citation = FieldList(StringField('Citation'), min_entries=0)
    # Origins
    origin = FieldList(StringField('Origin'), min_entries=0)
    # Datasets
    dataset = FieldList(StringField('Dataset'), min_entries=0)

    # Specified markers
    marker = FieldList(StringField('Specified Marker'), min_entries=0, label='Specified Marker')

    # Regulating markers
    regmarker = FieldList(FormField(RegMarkerEntryForm), min_entries=0, label='Regulating Marker')