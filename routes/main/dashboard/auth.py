from flask import render_template, request, redirect, url_for, session, Blueprint, jsonify
from werkzeug.security import check_password_hash
from core.database import db
from core.auth_helper import clear_admin_session
from datetime import datetime, timedelta

auth_bp = Blueprint('admin_auth_page', __name__, url_prefix='')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        from model.user import User

        # Accept either username or email
        login_input = request.form.get('login')
        password = request.form.get('password')

        # Validate input
        if not login_input or not password:
            return redirect(url_for('admin_auth_page.login',
                                    message='Please fill in all fields',
                                    type='error'))

        try:
            # Find user by username or email
            user = User.query.filter(
                (User.username == login_input) | (User.email == login_input)
            ).first()

            if user and check_password_hash(user.password, password):
                clear_admin_session()
                session['admin_user_id'] = user.id
                session['admin_username'] = user.username
                session['admin_email'] = user.email
                session['admin_profile_pic'] = user.profile_pic
                session['login_time'] = datetime.now().isoformat()  # Track login time
                session.permanent = True

                return redirect(url_for('admin.dashboard_route',
                                        message='Login successful! Welcome back.',
                                        type='success'))
            else:
                return redirect(url_for('admin_auth_page.login',
                                        message='Invalid username/email or password',
                                        type='error'))
        except Exception as e:
            return redirect(url_for('admin_auth_page.login',
                                    message='Database error: ' + str(e),
                                    type='error'))

    return render_template('dashboard/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    from model.user import User

    if User.query.count() > 0:
        return redirect(url_for('admin_auth_page.login',
                                message='Admin self-registration is disabled. Please use an existing administrator account.',
                                type='error'))

    if request.method == 'POST':
        from werkzeug.security import generate_password_hash

        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not all([username, email, password]):
            return redirect(url_for('admin_auth_page.register',
                                    message='All fields are required',
                                    type='error'))

        if password != confirm_password:
            return redirect(url_for('admin_auth_page.register',
                                    message='Passwords do not match',
                                    type='error'))

        if len(password) < 8:
            return redirect(url_for('admin_auth_page.register',
                                    message='Password must be at least 8 characters long',
                                    type='error'))

        existing = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing:
            return redirect(url_for('admin_auth_page.register',
                                    message='Username or email already exists',
                                    type='error'))

        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            profile_pic='default.png'
        )
        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('admin_auth_page.login',
                                    message='Account created successfully! Please login.',
                                    type='success'))
        except Exception as e:
            db.session.rollback()
            return redirect(url_for('admin_auth_page.register',
                                    message='Error creating account: ' + str(e),
                                    type='error'))

    return render_template('dashboard/register.html')

@auth_bp.route('/logout')
def logout():
    """Handle admin logout"""
    clear_admin_session()
    return redirect(url_for('admin_auth_page.login'))


# ============ SESSION MANAGEMENT ENDPOINTS ============

@auth_bp.route('/api/session-info')
def get_session_info():
    """Get current session information including time remaining"""
    from core.helpers import SessionWarning
    
    session_info = SessionWarning.get_session_info()
    
    if not session_info:
        return jsonify({'success': False, 'is_expired': True}), 401
    
    return jsonify({'success': True, **session_info})


@auth_bp.route('/api/refresh-session', methods=['POST'])
def refresh_session():
    """Refresh the session timeout"""
    if 'admin_user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    # Update login time to reset the timeout
    session['login_time'] = datetime.now().isoformat()
    session.modified = True
    
    return jsonify({
        'success': True,
        'message': 'Session refreshed',
        'new_timeout': (datetime.now() + timedelta(hours=1)).isoformat()
    })
