from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
import logging

# Create Blueprint
risk_bp = Blueprint('risk', __name__, template_folder='templates')

# Dummy data store
risk_assessments = [
    {
        'risk_id': 'RISK001',
        'company': 'Liberia Mining Co.',
        'risk_type': 'Tax Compliance Risk',
        'risk_level': 'High',
        'description': 'Significant decline in reported revenue',
        'mitigation_plan': 'Conduct detailed audit within 30 days',
        'assessed_by': 'risk_analyst_user',
        'assessed_date': '2025-04-10'
    }
]

# Dummy role check
def has_role(role):
    return current_user.is_authenticated and getattr(current_user, 'role', None) == role

# Dummy audit logger
def log_action(user, action, details):
    logging.info(f"{datetime.now()} - {user.username} - {action} - {details}")

# Route: List all risk assessments
@risk_bp.route('/')
@login_required
def list_risks():
    if not has_role('RISK_ANALYST') and not has_role('ADMIN'):
        flash("Access denied: insufficient permissions.", "danger")
        return redirect(url_for('auth.login'))
    log_action(current_user, 'VIEW_RISK_ASSESSMENTS', 'Viewed list of risk assessments')
    return render_template('risk_list.html', risk_assessments=risk_assessments)

# Route: Submit new risk assessment
@risk_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_risk():
    if not has_role('RISK_ANALYST'):
        flash("Access denied: insufficient permissions.", "danger")
        return redirect(url_for('risk.list_risks'))

    if request.method == 'POST':
        new_risk = {
            'risk_id': f"RISK{len(risk_assessments)+1:03d}",
            'company': request.form['company'],
            'risk_type': request.form['risk_type'],
            'risk_level': request.form['risk_level'],
            'description': request.form['description'],
            'mitigation_plan': request.form['mitigation_plan'],
            'assessed_by': current_user.username,
            'assessed_date': datetime.now().strftime('%Y-%m-%d')
        }
        risk_assessments.append(new_risk)
        log_action(current_user, 'SUBMIT_RISK_ASSESSMENT', f"Submitted risk {new_risk['risk_id']}")
        flash("Risk assessment submitted successfully.", "success")
        return redirect(url_for('risk.list_risks'))

    return render_template('risk_submit.html')

# Route: View risk assessment details
@risk_bp.route('/<risk_id>')
@login_required
def view_risk(risk_id):
    if not has_role('RISK_ANALYST') and not has_role('ADMIN'):
        flash("Access denied: insufficient permissions.", "danger")
        return redirect(url_for('risk.list_risks'))

    risk = next((r for r in risk_assessments if r['risk_id'] == risk_id), None)
    if not risk:
        flash("Risk assessment not found.", "warning")
        return redirect(url_for('risk.list_risks'))

    log_action(current_user, 'VIEW_RISK_DETAIL', f"Viewed risk {risk_id}")
    return render_template('risk_detail.html', risk=risk)