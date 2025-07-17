from enum import Enum
from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

class Role(Enum):
    ADMIN = 'admin'
    SUPERVISOR = 'supervisor'
    AUDITOR = 'auditor'
    USER = 'user'

# Define role hierarchy
ROLE_HIERARCHY = {
    Role.ADMIN: 4,
    Role.SUPERVISOR: 3,
    Role.AUDITOR: 2,
    Role.USER: 1
}

def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("auth.login"))

            try:
                user_role = Role(current_user.role)
            except ValueError:
                flash("Invalid user role.", "danger")
                return redirect(url_for("auth.login"))

            if ROLE_HIERARCHY.get(user_role, 0) < ROLE_HIERARCHY.get(required_role, 0):
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for("auth.login"))

            return f(*args, **kwargs)
        return decorated_function
    return decorator