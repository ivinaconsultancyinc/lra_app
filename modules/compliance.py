from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from modules.models import Compliance, db
from modules.forms import ComplianceForm

compliance_bp = Blueprint('compliance', __name__, template_folder='templates')

@compliance_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_compliance():
    form = ComplianceForm()
    if form.validate_on_submit():
        new_entry = Compliance(
            company=form.company.data,
            regulation=form.regulation.data,
            status=form.status.data,
            findings=form.findings.data,
            recommendations=form.recommendations.data,
            checked_by=form.checked_by.data,
            next_review_date=form.next_review_date.data
        )
        db.session.add(new_entry)
        db.session.commit()
        flash('Compliance check submitted successfully!', 'success')
        return redirect(url_for('compliance.submit_compliance'))
    return render_template('compliance_submit.html', form=form)

@compliance_bp.route('/')
@login_required
def index():
    entries = Compliance.query.order_by(Compliance.id.desc()).all()
    return render_template('compliance/compliance_index.html', entries=entries)



