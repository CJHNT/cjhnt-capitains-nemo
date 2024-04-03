from flask import request
from flask_wtf import FlaskForm
from flask_babel import lazy_gettext as _l
from flask_babel import _
from wtforms import StringField, BooleanField, SelectMultipleField, SelectField, SubmitField
from wtforms.validators import DataRequired, ValidationError
from wtforms.fields import IntegerField
from wtforms.widgets import CheckboxInput


def validate_optional_number_range(min=-1, max=-1, message=None):
    """ Allows the validation of integer fields with a required number range but that are also optional
        I could not get WTForms to invalidate an integer field where the value was not within the range if it had the
        Optional() validator. I think this must have seen this as an empty field and thus erased all previous validation
        results since it correctly invalidates invalid data when the Optional() validator is not included.
    """
    if not message:
        message = "Field value must between between %i and %i." % (min, max)

    def _length(form, field):
        if field.data:
            if int(field.data) < min or max != -1 and int(field.data) > max:
                raise ValidationError(message)

    return _length


class SearchForm(FlaskForm):
    q = StringField(_l('Suche'), validators=[DataRequired()])
    corpus = SelectMultipleField(_l('Corpora'), choices=[('new_testament', _l('NT')), ('jewish', _l('Jüdische Texte'))],
                                 option_widget=CheckboxInput(),
                                 validators=[DataRequired(
                                     message=_l('Sie müssen mindestens eine Sammlung für die Suche auswählen ("NT" und/oder "Jüdische Texte")'))]
                                 )

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False
        super(SearchForm, self).__init__(*args, **kwargs)


class AdvancedSearchForm(SearchForm):
    q = StringField(_l('Suche'))  # query string is not DataRequired here since someone might want to search on other criteria
    lemma_search = BooleanField(_l('Lemma'))
    fuzziness = SelectField(_l("Unschärfegrad"),
                            choices=[("0", '0'), ("1", "1"), ("2", '2'), ('AUTO', _('AUTO'))],
                            default="0")
    slop = IntegerField(_l("Suchradius"), default=0)
    in_order = BooleanField(_l('Wortreihenfolge beachten?'))
    corpus = SelectMultipleField(_l('Corpora'), choices=[])
    submit = SubmitField(_l('Suche'))
