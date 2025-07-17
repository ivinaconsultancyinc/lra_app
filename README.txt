LRA Flask Application - README
==============================

Overview:
---------
The LRA (Local Risk Assessment) Flask application is a web-based platform designed to manage compliance submissions, perform tax calculations, and enforce role-based access control. It supports multiple user roles such as ADMIN, SUPERVISOR, AUDITOR, and USER, each with different access privileges.

Structure:
----------
- app.py: Main application file that initializes the Flask app, database, routes, and blueprints.
- roles.py: Contains the Role enum and role_required decorator with role hierarchy logic.
- templates/: HTML templates for rendering views.
- static/: Static files like CSS and JavaScript.
- instance/: Contains the SQLite database (e.g., lra_app.db).

Setup Instructions:
-------------------
1. Install dependencies:
   pip install flask flask_sqlalchemy flask_login

2. Set environment variables:
   export FLASK_APP=app.py
   export FLASK_ENV=development

3. Initialize the database:
   from app import db
   db.create_all()

4. Run the application:
   flask run

