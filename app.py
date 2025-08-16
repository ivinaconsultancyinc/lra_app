# app.py

import os
import csv
import logging
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from logging.handlers import RotatingFileHandler

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

# VAT rates by country (keeping existing for backward compatibility)
VAT_RATES = {
    'US': 0.07,
    'UK': 0.20,
    'DE': 0.19,
    'FR': 0.20,
    'IN': 0.18,
    'CA': 0.05,
    'LR': 0.15  # Liberia VAT rate
}

# GST rates for Liberia Natural Resources (updated rates as of 2024)
LIBERIA_GST_RATES = {
    'standard': 0.15,  # Standard GST rate 15%
    'mining': 0.15,    # Mining operations
    'forestry': 0.15,  # Forestry operations
    'petroleum': 0.15, # Petroleum operations
    'gold': 0.15,      # Gold mining
    'iron_ore': 0.15,  # Iron ore mining
    'rubber': 0.15,    # Rubber plantations
    'palm_oil': 0.15,  # Palm oil operations
    'exempt': 0.00,    # Exempt items
    'zero_rated': 0.00 # Zero-rated items
}

# GST exempt and zero-rated categories for natural resources
GST_EXEMPT_ITEMS = [
    'raw_minerals_export',
    'unprocessed_timber_export',
    'crude_oil_export',
    'basic_food_items',
    'medical_supplies',
    'educational_materials'
]

GST_ZERO_RATED_ITEMS = [
    'exports_outside_liberia',
    'international_transport',
    'diplomatic_purchases'
]

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

class GSTCalculation(db.Model):
    __tablename__ = 'gst_calculations'
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    transaction_type = db.Column(db.String(50), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)
    gross_amount = db.Column(db.Float, nullable=False)
    gst_rate = db.Column(db.Float, nullable=False)
    gst_amount = db.Column(db.Float, nullable=False)
    net_amount = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    calculation_date = db.Column(db.DateTime, default=datetime.utcnow)
    calculated_by = db.Column(db.String(100))
    notes = db.Column(db.Text)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# GST Calculation Functions
def calculate_gst_inclusive(gross_amount, gst_rate):
    """Calculate GST when the gross amount includes GST"""
    net_amount = gross_amount / (1 + gst_rate)
    gst_amount = gross_amount - net_amount
    return {
        'net_amount': round(net_amount, 2),
        'gst_amount': round(gst_amount, 2),
        'total_amount': round(gross_amount, 2)
    }

def calculate_gst_exclusive(net_amount, gst_rate):
    """Calculate GST when the net amount excludes GST"""
    gst_amount = net_amount * gst_rate
    total_amount = net_amount + gst_amount
    return {
        'net_amount': round(net_amount, 2),
        'gst_amount': round(gst_amount, 2),
        'total_amount': round(total_amount, 2)
    }

def get_gst_rate_for_resource(resource_type, item_category=None):
    """Determine GST rate based on resource type and category"""
    if item_category in GST_EXEMPT_ITEMS:
        return 0.00
    elif item_category in GST_ZERO_RATED_ITEMS:
        return 0.00
    else:
        return LIBERIA_GST_RATES.get(resource_type, LIBERIA_GST_RATES['standard'])

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

    # Use safe writable path for SQLite database
    db_path = os.environ.get('DATABASE_PATH', '/tmp/lra_app.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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

    # Create tables
    with app.app_context():
        db.create_all()

    # Register blueprints (keeping existing ones)
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

    # Main dashboard
    @app.route('/')
    def index():
        return render_template('index.html')

    # GST Calculation Routes
    @app.route('/gst', methods=['GET'])
    @login_required
    def gst_form():
        return render_template('gst/gst_form.html', 
                             resource_types=list(LIBERIA_GST_RATES.keys()),
                             exempt_items=GST_EXEMPT_ITEMS,
                             zero_rated_items=GST_ZERO_RATED_ITEMS)

    @app.route('/calculate_gst', methods=['POST'])
    @login_required
    def calculate_gst():
        try:
            company_name = request.form.get('company_name')
            transaction_type = request.form.get('transaction_type')  # 'inclusive' or 'exclusive'
            resource_type = request.form.get('resource_type')
            item_category = request.form.get('item_category')
            amount = float(request.form.get('amount'))
            notes = request.form.get('notes', '')

            # Determine GST rate
            gst_rate = get_gst_rate_for_resource(resource_type, item_category)

            # Calculate GST based on transaction type
            if transaction_type == 'inclusive':
                result = calculate_gst_inclusive(amount, gst_rate)
            else:
                result = calculate_gst_exclusive(amount, gst_rate)

            # Save calculation to database
            calculation = GSTCalculation(
                company_name=company_name,
                transaction_type=transaction_type,
                resource_type=resource_type,
                gross_amount=amount,
                gst_rate=gst_rate,
                gst_amount=result['gst_amount'],
                net_amount=result['net_amount'],
                total_amount=result['total_amount'],
                calculated_by=current_user.email if current_user.is_authenticated else 'System',
                notes=notes
            )
            db.session.add(calculation)
            db.session.commit()

            return render_template('gst/gst_result.html',
                                 company_name=company_name,
                                 resource_type=resource_type,
                                 transaction_type=transaction_type,
                                 gst_rate=gst_rate * 100,  # Convert to percentage
                                 **result)

        except Exception as e:
            flash(f'Error calculating GST: {str(e)}', 'error')
            return redirect(url_for('gst_form'))

    @app.route('/gst_history')
    @login_required
    def gst_history():
        calculations = GSTCalculation.query.order_by(GSTCalculation.calculation_date.desc()).all()
        return render_template('gst/gst_history.html', calculations=calculations)

    @app.route('/api/gst_rates')
    def api_gst_rates():
        """API endpoint to get current GST rates"""
        return jsonify(LIBERIA_GST_RATES)

    @app.route('/bulk_gst_calculate', methods=['GET', 'POST'])
    @login_required
    def bulk_gst_calculate():
        """Bulk GST calculation for multiple transactions"""
        if request.method == 'GET':
            return render_template('gst/bulk_gst_form.html')
        
        try:
            transactions = request.json.get('transactions', [])
            results = []
            
            for transaction in transactions:
                resource_type = transaction.get('resource_type')
                item_category = transaction.get('item_category')
                transaction_type = transaction.get('transaction_type')
                amount = float(transaction.get('amount'))
                
                gst_rate = get_gst_rate_for_resource(resource_type, item_category)
                
                if transaction_type == 'inclusive':
                    result = calculate_gst_inclusive(amount, gst_rate)
                else:
                    result = calculate_gst_exclusive(amount, gst_rate)
                
                result['resource_type'] = resource_type
                result['gst_rate'] = gst_rate
                results.append(result)
            
            return jsonify({'success': True, 'results': results})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    # Enhanced tax calculation routes (keeping existing functionality)
    @app.route('/tax', methods=['GET'])
    def tax_form():
        return render_template('tax/tax_form.html')

    @app.route('/calculate_tax', methods=['POST'])
    def calculate_tax_post():
        country = request.form.get('country')
        amount = float(request.form.get('amount'))
        tax = round(amount * VAT_RATES.get(country.upper(), 0), 2)
        total = round(amount + tax, 2)
        return render_template('tax/tax_result.html', 
                             country=country.upper(), 
                             amount=amount, 
                             tax=tax, 
                             total=total)

    # Enhanced export functions
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

    @app.route('/export_gst_calculations_csv')
    @login_required
    def export_gst_calculations_csv():
        """Export GST calculations to CSV"""
        filepath = os.path.join('exports', f'gst_calculations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        with sqlite3.connect('instance/lra_app.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM gst_calculations")
            rows = cursor.fetchall()
            headers = [description[0] for description in cursor.description]
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)
        return send_file(filepath, as_attachment=True)

    return app

# Run the app
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)




