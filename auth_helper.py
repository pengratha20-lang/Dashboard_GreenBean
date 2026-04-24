from functools import wraps
from flask import session, redirect, url_for

def login_required(f):
    """Decorator for admin/dashboard routes requiring login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('admin_auth_page.login'))
        return f(*args, **kwargs)
    return decorated_function
