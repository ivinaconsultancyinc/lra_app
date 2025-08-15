class Compliance(db.Model):
        __tablename__ = 'compliance'
        id = db.Column(db.Integer, primary_key=True)
        company = db.Column(db.String(100), nullable=False)
        regulation = db.Column(db.String(100), nullable=False)
        status = db.Column(db.String(50), nullable=False)
        findings = db.Column(db.Text)
        recommendations = db.Column(db.Text)
        checked_by = db.Column(db.String(100))
        next_review_date = db.Column(db.String(10))
        class User(UserMixin, db.Model):
            id = db.Column(db.Integer, primary_key=True)
        email = db.Column(db.String(150), unique=True, nullable=False)
        password = db.Column(db.String(150), nullable=False)
        role = db.Column(db.String(20), nullable=False, default='user')
        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))
        # Role-based access control decorator
        # Setup logging
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/lra_app.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('LRA Natural Resources Management System startup')
            # Register Blueprints
from auth.routes import auth as auth_blueprint
from modules.tax_audit import tax_audit_bp
from modules.transfer_pricing import tp_bp
from modules.compliance import compliance_bp
app.register_blueprint(auth_blueprint, url_prefix='/auth')
app.register_blueprint(tax_audit_bp, url_prefix='/tax_audit')
app.register_blueprint(risk_bp, url_prefix='/risk')
app.register_blueprint(tp_bp, url_prefix='/transfer_pricing')
app.register_blueprint(compliance_bp, url_prefix='/compliance')
            # VAT rates by country
VAT_RATES = {
    'US': 0.07,
    'UK': 0.20,
    'DE': 0.19,
    'FR': 0.20,
    'IN': 0.18,
    'CA': 0.05
    }
        # Tax calculation function
def calculate_tax(country_code, amount):
        rate = VAT_RATES.get(country_code.upper(), 0)
        return round(amount * rate, 2)
        # Route to display the tax form
@app.route('/tax', methods=['GET'])
def tax_form():
        return render_template('tax/tax_form.html')
        # Route to handle tax calculation and display result
@app.route('/calculate_tax', methods=['POST'])
def calculate_tax_post():
        country = request.form.get('country')
        amount = float(request.form.get('amount'))
        tax = calculate_tax(country, amount)
        total = round(amount + tax, 2)
        return render_template('tax/tax_result.html', country=country.upper(), amount=amount, tax=tax, total=total)
@app.route('/admin')
@login_required
@role_required('admin')
def admin_dashboard():
        return render_template('admin_dashboard.html')
@app.route('/export_compliance_csv')
@login_required
@role_required('admin')
def export_compliance_csv():
            # Ensure the exports directory exists
            export_dir = os.path.join(os.getcwd(), 'exports')
            os.makedirs(export_dir, exist_ok=True)
                # Generate timestamped filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'compliance_export_{timestamp}.csv'
            filepath = os.path.join(export_dir, filename)
                # Connect to the SQLite database
            db_path = os.path.join(os.getcwd(), 'instance', 'lra_app.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
                # Fetch all data from compliance table
            cursor.execute("SELECT * FROM compliance")
            rows = cursor.fetchall()
                # Get column headers
            headers = [description[0] for description in cursor.description]
                # Write to CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)
                conn.close()
                # Return the file as a download
            return send_file(filepath, as_attachment=True)
            return app

from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from functools import wraps
        import logging
from logging.handlers import RotatingFileHandler
        import os
        # Initialize extensions
        db = SQLAlchemy()
        login_manager = LoginManager()
def create_app():
        app = Flask(__name__)
                # Configuration
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'supersecretkey')
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/lra_app.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
            # Initialize extensions
        db.init_app(app)
        login_manager.init_app(app)
        login_manager.login_view = 'auth.login'
        # User model with role
        # Compliance model
# --- Begin Integrated Code from routes.py ---
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from modules.models import User, db
from roles import Role, role_required
auth = Blueprint('auth', __name__, template_folder='templates')
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('login.html')
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
                email=email,
                role=role,
                password=generate_password_hash(password, method='sha256'),
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
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
# --- End Integrated Code from routes.py ---
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)












