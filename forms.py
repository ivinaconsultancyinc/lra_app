from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired

class ComplianceForm(FlaskForm):
    company = StringField('Company', validators=[DataRequired()])
    regulation = StringField('Regulation', validators=[DataRequired()])
    status = SelectField('Status', choices=[('Compliant', 'Compliant'), ('Non-Compliant', 'Non-Compliant')], validators=[DataRequired()])
    findings = TextAreaField('Findings')
    recommendations = TextAreaField('Recommendations')
    checked_by = StringField('Checked By')
    next_review_date = DateField('Next Review Date', format='%Y-%m-%d')
    submit = SubmitField('Submit')