"""
Form used to create and update Senotype JSONs.
"""


from wtforms import (Form, SelectField, validators, ValidationError,
                     TextAreaField, FieldList, StringField, FormField, RadioField)
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


def validate_age(val) -> str:

    """
    Custom validator for age.

    Assumes that age unit is years.

    """

    if val is None:
        return "ok"
    if val < 0:
        return 'Age must be positive.'
    if val > 90:
        return 'Ages over 89 years must be set to 90 years.'

    return "ok"


def validate_age_range(form, field):
    """
    Validates that:
    1. The age value, lowerbound, and upperbound are all ages.
    1. The lowerbound is less than both the value and upperbound.
    2. The age value is less than the upperbound.

    Assumes that the validateage validator is called prior.

    """

    agevalue = to_num(form.agevalue.data)
    lowerbound = to_num(form.agelowerbound.data)
    upperbound = to_num(form.ageupperbound.data)

    valuevalidate = validate_age(agevalue)
    lowerboundvalidate = validate_age(lowerbound)
    upperboundvalidate = validate_age(upperbound)

    if valuevalidate == "ok" and lowerboundvalidate == "ok" and upperboundvalidate == "ok":
        if lowerbound is not None and agevalue is not None and lowerbound > agevalue:
            raise ValidationError('The age must be >= the age lower bound.')
        if agevalue is not None and upperbound is not None and agevalue > upperbound:
            raise ValidationError('The age must be <= the age upper bound.')
        if lowerbound is not None and upperbound is not None and lowerbound > upperbound:
            raise ValidationError('The age lower bound must be <= the age upper bound.')
    else:
        errors = ';'.join(s for s in [valuevalidate, lowerboundvalidate, upperboundvalidate] if s != "ok")
        raise ValidationError(errors)


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
    senotypename = TextAreaField('Name', validators=[validators.InputRequired()])
    senotypedescription = TextAreaField('Description', validators=[validators.InputRequired()])
    doi = TextAreaField('DOI')

    # Provenance and version
    provenance = FieldList(StringField('Provenance ID'), min_entries=0)

    # Submitter
    submitterfirst = StringField('First', validators=[validators.InputRequired()])
    submitterlast = StringField('Last', validators=[validators.InputRequired()])
    submitteremail = StringField('email', validators=[validators.InputRequired(), Email(message='Invalid email address.')])

    # Simple assertions.
    # These lists require custom validators because they will be updated via Javascript.
    taxon = FieldList(StringField('Taxon'), min_entries=0, label='Taxon')
    location = FieldList(StringField('Location'), min_entries=0)
    celltype = FieldList(StringField('Cell type'), min_entries=0)
    hallmark = FieldList(StringField('Hallmark'), min_entries=0)
    inducer = FieldList(StringField('Inducer'), min_entries=0)
    assay = FieldList(StringField('Assay'), min_entries=0)

    # The FTU input will use a jstree control.
    ftu = SelectField('FTU path', choices=[])

    # Context assertions
    agevalue = StringField('Value', validators=[validate_age_range])
    agelowerbound = StringField('Lowerbound', validators=[validate_age_range])
    ageupperbound = StringField('Upperbound', validators=[validate_age_range])
    ageunit = StringField('Unit')
    ageunit.data = 'year'

    bmivalue = StringField('Value')
    bmilowerbound = StringField('Lowerbound')
    bmiupperbound = StringField('Upperbound')
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