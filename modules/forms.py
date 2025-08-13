from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField
from wtforms.validators import DataRequired

class ComplianceForm(FlaskForm):
    company = StringField('Company', validators=[DataRequired()])
    regulation = StringField('Regulation', validators=[DataRequired()])
    status = StringField('Status', validators=[DataRequired()])
    findings = TextAreaField('Findings')
    recommendations = TextAreaField('Recommendations')
    checked_by = StringField('Checked By')
    next_review_date = DateField('Next Review Date', format='%Y-%m-%d')

