"""
Form used to create and update Senotype JSONs.
"""

from wtforms import (Form, SelectField, validators, ValidationError,
                     TextAreaField, FieldList, StringField, FormField, HiddenField)
from wtforms.validators import Email

# Helper classes
from models.appconfig import AppConfig
from models.senlib import SenLib
from models.stringnumber import stringisintegerorfloat


def to_num(val):
    # Tests whether strings are numbers.
    if val is None or val == "":
        return None
    try:
        return float(val)
    except ValueError:
        raise ValidationError("Ages must be numbers.")


def validate_numeric(val:float, field_name:str, rangemin: float=0, rangemax: float=100) -> str:

    """
    Custom validator for a numeric field.
    :param val: the value to validate
    :param field_name: the field name
    :param rangemin: the lower bound of the range
    :param rangemax: the upper bound of the range

    """

    if val is None:
        return 'ok'
    if val < rangemin:
        return f'The minimum value of {field_name} is {str(rangemin)}.'
    if rangemax is not None:
        if val > rangemax:
            return f'The maximum value of {field_name} is {str(rangemax)}.'
    else:
        return 'ok'

    return 'ok'


def validate_range(form, field):
    """
    Validates for a set of context fields (age, BMI) that:
    1. The value, lowerbound, and upperbound are all ages.
    1. The lowerbound is less than both the value and upperbound.
    2. The value is less than the upperbound.

    Both the form and field parameters are required by WTForms.

    """

    isage = field.name in ['agevalue', 'agelowerbound', 'ageupperbound']
    isbmi = field.name in ['bmivalue', 'bmilowerbound', 'bmiupperbound']

    if isage:
        valuedisplay = 'age'
        rangevalue = to_num(form.agevalue.data)
        rangelowerbound = to_num(form.agelowerbound.data)
        rangeupperbound = to_num(form.ageupperbound.data)
        # Maximum age
        rangemax = 89

    elif isbmi:
        # BMI
        valuedisplay = 'BMI'
        rangevalue = to_num(form.bmivalue.data)
        rangelowerbound = to_num(form.bmilowerbound.data)
        rangeupperbound = to_num(form.bmiupperbound.data)
        rangemax = 100
    else:
        raise ValidationError(f'Unknown field for validator: {field.name}')

    # Validate that all values in the set are numeric and non-negative.
    valuevalidate = validate_numeric(val=rangevalue, field_name=valuedisplay, rangemax=rangemax)
    lowerboundvalidate = validate_numeric(val=rangelowerbound, field_name='lowerbound', rangemax=rangemax)
    upperboundvalidate = validate_numeric(val=rangeupperbound, field_name='upperbound', rangemax=rangemax)

    if valuevalidate == "ok" and lowerboundvalidate == "ok" and upperboundvalidate == "ok":

        # Validate that lowerbound <= value <= upperbound.
        # Display an error next to only one of the three fields.
        if (rangevalue is not None
                and rangelowerbound is not None
                and rangelowerbound > rangevalue
                and 'value' in field.name):
            raise ValidationError(f'{valuedisplay} must be >=  lower bound.')

        if (rangevalue is not None
                and rangeupperbound is not None
                and rangevalue > rangeupperbound
                and 'value' in field.name):
            raise ValidationError(f'{valuedisplay} must be <= upper bound.')

        if (rangelowerbound is not None
                and rangeupperbound is not None
                and rangelowerbound > rangeupperbound
                and 'lowerbound' in field.name) :
            raise ValidationError('lower bound must be <= the upper bound.')

    else:
        # Display numeric validation error next to the field with the error.
        if valuevalidate != 'ok' and 'value' in field.name:
            raise ValidationError(valuevalidate)
        if lowerboundvalidate != 'ok' and 'lowerbound' in field.name:
            raise ValidationError(lowerboundvalidate)
        if upperboundvalidate != 'ok' and 'upperbound' in field.name:
            raise ValidationError(upperboundvalidate)


def validate_number(field):
    """
    Custom validator for StringFields that collect numeric data.
    :param field: the field to check
    :return: Nothing or raises ValidationError
    """

    valuetotest = field.data
    if valuetotest is None:
        return

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
    if valuetotest is None:
        return

    test = stringisintegerorfloat(valuetotest)

    if test != "integer":
        raise ValidationError(f'{field.name} must be an integer.')


# ----------------------
# MAIN FORM

class RegMarkerEntryForm(Form):

    """
    Custom form class for regulating markers, which store data in two hidden inputs:
    - the marker code
    - the regulating action
    """

    marker = StringField('Regulating Marker')
    action = StringField('Regulating Action')


class EditForm(Form):

    # Set up the Senlib interface to obtain valueset information.

    # SENOTYPE TREEVIEW

    # The features of the Senotype treeview depend on whether the user is authorized
    # to edit senotype JSONs. The authorization compares the user's email address
    # from Globus (in a session variable) with the email stored with a Senotype JSON.
    def __init__(self, *args, **kwargs):
        super(EditForm, self).__init__(*args, **kwargs)
        # Import session in the method to avoid issues outside request context
        from flask import session
        self.senlib = SenLib(cfg=AppConfig(), userid=session.get('userid', ''))

    # SET DEFAULTS FOR FIELDS

    # Senotype
    senotypeid = StringField('ID')
    senotypename = TextAreaField('Name', validators=[validators.InputRequired(message="The Senotype name is required.")])
    senotypedescription = TextAreaField('Description', validators=[validators.InputRequired(message="The Senotype description is required.")])
    doi = TextAreaField('DOI')

    # Provenance and version
    provenance = FieldList(StringField('Provenance ID'), min_entries=0)

    # Submitter
    submitterfirst = StringField('First', validators=[validators.InputRequired()])
    submitterlast = StringField('Last', validators=[validators.InputRequired()])
    submitteremail = StringField('email', validators=[validators.InputRequired(),
                                                      Email(message='Invalid email address.')])

    # Simple assertions.
    # These lists require custom validators because they will be updated via Javascript.
    taxon = FieldList(StringField('Taxon'), min_entries=0, label='Taxon')
    location = FieldList(StringField('Location'), min_entries=0)
    celltype = FieldList(StringField('Cell type'), min_entries=0)
    microenvironment = FieldList(StringField('Microenvironment'), min_entries=0)
    hallmark = FieldList(StringField('Hallmark'), min_entries=0)
    inducer = FieldList(StringField('Inducer'), min_entries=0)
    assay = FieldList(StringField('Assay'), min_entries=0)

    # Context assertions
    agevalue = StringField('Value', validators=[validate_range])
    agelowerbound = StringField('Lower', validators=[validate_range])
    ageupperbound = StringField('Upper', validators=[validate_range])
    ageunit = StringField('Unit')
    ageunit.data = 'year'

    bmivalue = StringField('Value', validators=[validate_range])
    bmilowerbound = StringField('Lower', validators=[validate_range])
    bmiupperbound = StringField('Upper', validators=[validate_range])
    bmiunit = StringField('Unit')
    bmiunit.data = 'kg/m2'

    sex = FieldList(StringField('Sex'), min_entries=0, label='Sex')

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

    # Hidden field used to validate whether at least one FTU path was selected.
    # This field works with the update-button.js and the update route.
    # ftu_tree_json = HiddenField('FTU Tree JSON')

    # Diagnosis
    diagnosis = FieldList(StringField('Diagnosis'), min_entries=0)
