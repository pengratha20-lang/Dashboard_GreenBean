from functools import wraps
from flask import redirect, session, url_for

ADMIN_SESSION_ID_KEY = 'admin_user_id'
CUSTOMER_SESSION_ID_KEY = 'customer_id'


def is_admin_logged_in():
    return ADMIN_SESSION_ID_KEY in session


def is_customer_logged_in():
    return CUSTOMER_SESSION_ID_KEY in session


def get_customer_session_id():
    return session.get(CUSTOMER_SESSION_ID_KEY)


def clear_admin_session():
    for key in ['admin_user_id', 'admin_username', 'admin_email', 'admin_profile_pic']:
        session.pop(key, None)


def clear_customer_session():
    for key in ['customer_id', 'customer_name', 'customer_email', 'remember_me', 'cart_merge_required', 'cart', 'coupon_code']:
        session.pop(key, None)


def login_required(f):
    """Decorator for admin/dashboard routes requiring an admin login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin_logged_in():
            return redirect(url_for('admin_auth_page.login'))
        return f(*args, **kwargs)
    return decorated_function
