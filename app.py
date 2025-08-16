# app.py

import os
import csv
import logging
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from logging.handlers import RotatingFileHandler

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

# VAT rates by country
VAT_RATES = {
    'US': 0.07,
    'UK': 0.20,
    'DE': 0.19,
    'FR': 0.20,
    'IN': 0.18,
    'CA': 0.05
}

# Models
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

# Create app
def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'supersecretkey')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/lra_app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Ensure required directories exist
    os.makedirs('logs', exist_ok=True)
    os.makedirs('instance', exist_ok=True)
    os.makedirs('exports', exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Logging setup
    file_handler = RotatingFileHandler('logs/lra_app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('LRA Natural Resources Management System startup')

    # Register blueprints
    from auth.routes import auth as auth_blueprint
    from modules.tax_audit import tax_audit_bp
    from modules.transfer_pricing import tp_bp
    from modules.compliance import compliance_bp
    from modules.risk import risk_bp

    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(tax_audit_bp, url_prefix='/tax_audit')
    app.register_blueprint(tp_bp, url_prefix='/transfer_pricing')
    app.register_blueprint(compliance_bp, url_prefix='/compliance')
    app.register_blueprint(risk_bp, url_prefix='/risk')

    # Tax calculation routes
    @app.route('/tax', methods=['GET'])
    def tax_form():
        return render_template('tax/tax_form.html')

    @app.route('/calculate_tax', methods=['POST'])
    def calculate_tax_post():
        country = request.form.get('country')
        amount = float(request.form.get('amount'))
        tax = round(amount * VAT_RATES.get(country.upper(), 0), 2)
        total = round(amount + tax, 2)
        return render_template('tax/tax_result.html', country=country.upper(), amount=amount, tax=tax, total=total)

    # Export compliance data to CSV
    @app.route('/export_compliance_csv')
    @login_required
    def export_compliance_csv():
        filepath = os.path.join('exports', f'compliance_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        with sqlite3.connect('instance/lra_app.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM compliance")
            rows = cursor.fetchall()
            headers = [description[0] for description in cursor.description]
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)
        return send_file(filepath, as_attachment=True)

    return app

# Run the app
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
