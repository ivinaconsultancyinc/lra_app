from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from modules.models import User, db

auth = Blueprint('auth', __name__, template_folder='templates')

@auth.route('/login', methods=['_template('login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'warning')
        else:
            new_user = User(
                user                email=email,
                role=role,
                password_hash=generate_password_hash(password, method='sha256')
            )
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('auth.login'))
    return render_template('register.html')

@app.route('/compliance/submit', methods=['GET', 'POST'])
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
        return redirect(url_for('submit_compliance'))
    return render_template('compliance_submit.html', form=form)


@auth.route('/logout')
@login_required
defYou have been logged out.', 'info')
    return redirect(url_for('auth.login'))