from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')

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

