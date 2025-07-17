from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
import logging

# Create Blueprint
tp_bp = Blueprint('transfer_pricing', __name__, template_folder='templates')

# Dummy data store
tp_analyses = [
    {
        'analysis_id': 'TP001',
        'company': 'Liberia Mining Co.',
        'transaction_type': 'Sale of Iron Ore',
        'related_party': 'Parent Company',
        'transaction_value_usd': 25000000,
        'arm_length_price_usd': 26000000,
        'adjustment_required': True,
        'analysis_method': 'Comparable Uncontrolled Price',
        'analyst': 'analyst_user',
        'submitted_date': '2025-04-20'
    }
]

# Dummy role check
def has_role(role):
    return current_user.is_authenticated and getattr(current_user, 'role', None) == role

# Dummy audit logger
def log_action(user, action, details):
    logging.info(f"{datetime.now()} - {user.username} - {action} - {details}")

# Route: List all transfer pricing analyses
@tp_bp.route('/')
@login_required
def list_tp_analyses():
    if not has_role('TRANSFER_PRICING_SPECIALIST') and not has_role('ADMIN'):
        flash("Access denied: insufficient permissions.", "danger")
        return redirect(url_for('auth.login'))
    log_action(current_user, 'VIEW_TP_ANALYSES', 'Viewed list of transfer pricing analyses')
    return render_template('tp_list.html', tp_analyses=tp_analyses)

# Route: Submit new transfer pricing analysis
@tp_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_tp_analysis():
    if not has_role('TRANSFER_PRICING_SPECIALIST'):
        flash("Access denied: insufficient permissions.", "danger")
        return redirect(url_for('transfer_pricing.list_tp_analyses'))

    if request.method == 'POST':
        new_analysis = {
            'analysis_id': f"TP{len(tp_analyses)+1:03d}",
            'company': request.form['company'],
            'transaction_type': request.form['transaction_type'],
            'related_party': request.form['related_party'],
            'transaction_value_usd': float(request.form['transaction_value_usd']),
            'arm_length_price_usd': float(request.form['arm_length_price_usd']),
            'adjustment_required': request.form.get('adjustment_required') == 'True',
            'analysis_method': request.form['analysis_method'],
            'analyst': current_user.username,
            'submitted_date': datetime.now().strftime('%Y-%m-%d')
        }
        tp_analyses.append(new_analysis)
        log_action(current_user, 'SUBMIT_TP_ANALYSIS', f"Submitted analysis {new_analysis['analysis_id']}")
        flash("Transfer pricing analysis submitted successfully.", "success")
        return redirect(url_for('transfer_pricing.list_tp_analyses'))

    return render_template('tp_submit.html')

# Route: View transfer pricing analysis details
@tp_bp.route('/<analysis_id>')
@login_required
def view_tp_analysis(analysis_id):
    if not has_role('TRANSFER_PRICING_SPECIALIST') and not has_role('ADMIN'):
        flash("Access denied: insufficient permissions.", "danger")
        return redirect(url_for('transfer_pricing.list_tp_analyses'))

    analysis = next((a for a in tp_analyses if a['analysis_id'] == analysis_id), None)
    if not analysis:
        flash("Transfer pricing analysis not found.", "warning")
        return redirect(url_for('transfer_pricing.list_tp_analyses'))

    log_action(current_user, 'VIEW_TP_ANALYSIS_DETAIL', f"Viewed analysis {analysis_id}")
    return render_template('tp_detail.html', analysis=analysis)



