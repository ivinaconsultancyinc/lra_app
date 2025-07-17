from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
import logging

# Create Blueprint
tax_audit_bp = Blueprint('tax_audit', __name__, template_folder='templates')

# Dummy data store
tax_returns = [
    {
        'return_id': 'TR001',
        'company': 'Liberia Mining Co.',
        'tax_period': '2025-Q1',
        'revenue_usd': 5000000,
        'revenue_lrd': 950000000,
        'tax_due_usd': 500000,
        'tax_due_lrd': 95000000,
        'filed_date': '2025-04-15'
    }
]

# Dummy role check
def has_role(role):
    return current_user.is_authenticated and getattr(current_user, 'role', None) == role

# Dummy audit logger
def log_action(user, action, details):
    logging.info(f"{datetime.now()} - {user.username} - {action} - {details}")

# Route: View all tax returns
@tax_audit_bp.route('/')
@login_required
def list_tax_returns():
    if not has_role('TAX_AUDITOR') and not has_role('ADMIN'):
        flash("Access denied: insufficient permissions.", "danger")
        return redirect(url_for('auth.login'))
    log_action(current_user, 'VIEW_TAX_RETURNS', 'Viewed list of tax returns')
    return render_template('tax_audit.html', tax_returns=tax_returns)

# Route: Submit new tax return
@tax_audit_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_tax_return():
    if not has_role('TAX_AUDITOR'):
        flash("Access denied: insufficient permissions.", "danger")
        return redirect(url_for('tax_audit.list_tax_returns'))

    if request.method == 'POST':
        new_return = {
            'return_id': f"TR{len(tax_returns)+1:03d}",
            'company': request.form['company'],
            'tax_period': request.form['tax_period'],
            'revenue_usd': float(request.form['revenue_usd']),
            'revenue_lrd': float(request.form['revenue_lrd']),
            'tax_due_usd': float(request.form['tax_due_usd']),
            'tax_due_lrd': float(request.form['tax_due_lrd']),
            'filed_date': datetime.now().strftime('%Y-%m-%d')
        }
        tax_returns.append(new_return)
        log_action(current_user, 'SUBMIT_TAX_RETURN', f"Submitted return {new_return['return_id']}")
        flash("Tax return submitted successfully.", "success")
        return redirect(url_for('tax_audit.list_tax_returns'))

    return render_template('submit_tax_return.html')

# Route: View tax return details
@tax_audit_bp.route('/<return_id>')
@login_required
def view_tax_return(return_id):
    if not has_role('TAX_AUDITOR') and not has_role('ADMIN'):
        flash("Access denied: insufficient permissions.", "danger")
        return redirect(url_for('tax_audit.list_tax_returns'))

    tax_return = next((r for r in tax_returns if r['return_id'] == return_id), None)
    if not tax_return:
        flash("Tax return not found.", "warning")
        return redirect(url_for('tax_audit.list_tax_returns'))

    log_action(current_user, 'VIEW_TAX_RETURN_DETAIL', f"Viewed return {return_id}")
    return render_template('tax_return_detail.html', tax_return=tax_return)