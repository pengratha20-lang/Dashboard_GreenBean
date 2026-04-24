from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from model.customer import Customer
from model.audit_log import LoginAttempt
from core.database import db
from datetime import timedelta, datetime
from core.auth_helper import clear_customer_session, get_customer_session_id, is_customer_logged_in
from core.validators import validate_email, validate_password, validate_string
from core.exceptions import ValidationError, InvalidEmail, DuplicateEntry
from core.security import security_logger, app_logger
from config.constants import SESSION_CONFIG, SECURITY_CONFIG

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle customer login with security logging"""
    login_error = None
    login_success = None
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not email or not password:
            login_error = 'Email and password are required.'
            security_logger.log_suspicious_activity(
                'login_missing_fields',
                ip_address=request.remote_addr
            )
            return render_template('frontside/auth/login.html', 
                                 title='Green Bean - Login',
                                 login_error=login_error), 400
        
        try:
            # Validate email format
            email = validate_email(email)
            
            # Try to find customer
            customer = Customer.query.filter_by(email=email).first()
            
            if customer and check_password_hash(customer.password, password):
                # Log successful login
                login_attempt = LoginAttempt(
                    username=email,
                    ip_address=request.remote_addr,
                    success=True,
                    user_id=customer.id,
                    user_type='customer'
                )
                db.session.add(login_attempt)
                db.session.commit()
                
                security_logger.log_session_lifecycle(
                    'login',
                    user_id=customer.id,
                    session_type='customer'
                )
                
                clear_customer_session()
                session[SESSION_CONFIG['CUSTOMER_SESSION_KEY']] = customer.id
                session['customer_name'] = customer.name
                session['customer_email'] = customer.email
                session[SESSION_CONFIG['CART_MERGE_FLAG']] = True
                
                session.permanent = False
                session.modified = True
                
                flash(f'Welcome back, {customer.name}!', 'success')
                return redirect(request.args.get('next') or url_for('home.home'))
            else:
                # Log failed login
                login_attempt = LoginAttempt(
                    username=email,
                    ip_address=request.remote_addr,
                    success=False,
                    failure_reason='invalid_credentials' if not customer else 'invalid_password',
                    user_id=customer.id if customer else None,
                    user_type='customer'
                )
                db.session.add(login_attempt)
                db.session.commit()
                
                security_logger.log_authentication_attempt(email, False, request.remote_addr)
                
                # More specific error message
                if customer:
                    login_error = 'Incorrect password. Please try again.'
                else:
                    login_error = 'Email not found. Please check your email or register a new account.'
                
                return render_template('frontside/auth/login.html', 
                                     title='Green Bean - Login',
                                     login_error=login_error), 400
        
        except InvalidEmail:
            login_error = 'Invalid email format. Please enter a valid email address.'
            security_logger.log_suspicious_activity(
                'login_invalid_email',
                details=f'Attempted: {email}',
                ip_address=request.remote_addr
            )
            return render_template('frontside/auth/login.html', 
                                 title='Green Bean - Login',
                                 login_error=login_error), 400
        except ValidationError as ve:
            login_error = ve.message
            return render_template('frontside/auth/login.html', 
                                 title='Green Bean - Login',
                                 login_error=login_error), 400
        except Exception as e:
            app_logger.log_error('LoginError', str(e))
            error_msg = str(e)
            if 'email' in error_msg.lower():
                login_error = 'Email validation error. Please check your email format.'
            elif 'password' in error_msg.lower():
                login_error = 'Password validation error. Please try again.'
            else:
                login_error = f'Error: {error_msg}' if len(error_msg) < 100 else 'Login error. Please try again.'
            return render_template('frontside/auth/login.html', 
                                 title='Green Bean - Login',
                                 login_error=login_error), 400
    
    return render_template('frontside/auth/login.html', title='Green Bean - Login')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle customer registration with validation"""
    register_error = None
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        terms = request.form.get('terms')
        
        try:
            # Validate all inputs
            if not all([name, email, password, confirm_password]):
                register_error = 'All fields are required.'
                return render_template('frontside/auth/register.html',
                                     title='Green Bean - Register',
                                     register_error=register_error), 400
            
            # Validate terms checkbox
            if not terms:
                register_error = 'You must agree to the Terms & Conditions to register.'
                return render_template('frontside/auth/register.html',
                                     title='Green Bean - Register',
                                     register_error=register_error), 400
            
            # Validate name
            name = validate_string(name, 'Name', min_length=2, max_length=100)
            
            # Validate email
            email = validate_email(email)
            
            # Validate passwords match
            if password != confirm_password:
                register_error = 'Passwords do not match.'
                return render_template('frontside/auth/register.html',
                                     title='Green Bean - Register',
                                     register_error=register_error), 400
            
            # Validate password strength
            password = validate_password(password)
            
            # Check if email already exists
            existing_customer = Customer.query.filter_by(email=email).first()
            if existing_customer:
                security_logger.log_suspicious_activity(
                    'duplicate_registration_attempt',
                    details=f'Email: {email}',
                    ip_address=request.remote_addr
                )
                register_error = 'Email already registered. Please login or use a different email.'
                return render_template('frontside/auth/register.html',
                                     title='Green Bean - Register',
                                     register_error=register_error), 400
            
            # Hash password and create new customer
            hashed_password = generate_password_hash(password)
            new_customer = Customer(
                name=name,
                email=email,
                password=hashed_password
            )
            
            db.session.add(new_customer)
            db.session.commit()
            
            # Log successful registration
            security_logger.log_session_lifecycle(
                'signup',
                user_id=new_customer.id,
                session_type='customer'
            )
            
            clear_customer_session()
            session[SESSION_CONFIG['CUSTOMER_SESSION_KEY']] = new_customer.id
            session['customer_name'] = new_customer.name
            session['customer_email'] = new_customer.email
            session[SESSION_CONFIG['CART_MERGE_FLAG']] = True
            
            session.permanent = False
            session.modified = True
            
            flash('Registration successful! Welcome to Green Bean!', 'success')
            return redirect(url_for('home.home'))
        
        except ValidationError as ve:
            register_error = ve.message
            security_logger.log_suspicious_activity(
                'registration_validation_error',
                details=f'Field: {ve.field}',
                ip_address=request.remote_addr
            )
            return render_template('frontside/auth/register.html',
                                 title='Green Bean - Register',
                                 register_error=register_error), 400
        except InvalidEmail as ie:
            register_error = str(ie)
            return render_template('frontside/auth/register.html',
                                 title='Green Bean - Register',
                                 register_error=register_error), 400
        except DuplicateEntry as de:
            register_error = str(de)
            return render_template('frontside/auth/register.html',
                                 title='Green Bean - Register',
                                 register_error=register_error), 400
        except Exception as e:
            db.session.rollback()
            app_logger.log_error('RegistrationError', str(e))
            # Include actual error message for debugging
            error_msg = str(e)
            if 'password' in error_msg.lower():
                register_error = 'Password does not meet security requirements. Use at least 8 characters with uppercase, lowercase, numbers, and symbols.'
            elif 'email' in error_msg.lower():
                register_error = 'Invalid email address. Please check and try again.'
            elif 'name' in error_msg.lower():
                register_error = 'Name must be between 2 and 100 characters.'
            else:
                register_error = f'Error: {error_msg}' if len(error_msg) < 100 else 'Registration error. Please try again.'
            return render_template('frontside/auth/register.html',
                                 title='Green Bean - Register',
                                 register_error=register_error), 400
    
    return render_template('frontside/auth/register.html', title='Green Bean - Register')


@auth_bp.route('/logout')
def logout():
    """Handle customer logout with security logging"""
    user_id = get_customer_session_id()
    
    # Log logout event
    security_logger.log_session_lifecycle(
        'logout',
        user_id=user_id,
        session_type='customer'
    )
    
    clear_customer_session()
    session.pop('cart', None)
    session.pop('coupon_code', None)
    session.pop(SESSION_CONFIG['CART_MERGE_FLAG'], None)
    session.modified = True
    
    flash('You have been logged out.', 'info')
    return redirect(url_for('home.home'))


@auth_bp.route('/check-session', methods=['GET'])
def check_session():
    """Check if user session is still valid"""
    if is_customer_logged_in():
        return jsonify({
            'valid': True,
            'user_name': session.get('customer_name', 'User'),
            'user_id': session.get('customer_id')
        })
    else:
        return jsonify({
            'valid': False,
            'message': 'Session expired'
        }), 401


@auth_bp.route('/refresh-session', methods=['POST'])
def refresh_session():
    """Refresh user session on activity"""
    if not is_customer_logged_in():
        return jsonify({
            'success': False,
            'message': 'Not logged in'
        }), 401
    
    try:
        # Check if customer still exists
        customer = Customer.query.get(get_customer_session_id())
        if not customer:
            clear_customer_session()
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Refresh session
        session.modified = True
        
        return jsonify({
            'success': True,
            'message': 'Session refreshed',
            'user_name': customer.name
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@auth_bp.route('/profile')
def profile():
    """View and edit customer profile"""
    if not is_customer_logged_in():
        flash('Please login first.', 'warning')
        return redirect(url_for('customer_auth.login', next=url_for('customer_auth.profile')))
    
    try:
        customer = Customer.query.get(get_customer_session_id())
        if not customer:
            clear_customer_session()
            flash('Session expired. Please login again.', 'warning')
            return redirect(url_for('customer_auth.login'))
        
        return render_template('frontside/auth/profile.html', title='My Account - Green Bean', customer=customer)
    except Exception as e:
        flash(f'Error loading profile: {str(e)}', 'danger')
        return redirect(url_for('home.home'))


@auth_bp.route('/profile/update', methods=['POST'])
def update_profile():
    """Update customer profile information - returns JSON for AJAX"""
    if not is_customer_logged_in():
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    try:
        customer = Customer.query.get(get_customer_session_id())
        if not customer:
            return jsonify({'success': False, 'message': 'Customer not found'}), 404
        
        # Get and validate name
        name = request.form.get('name', '').strip()
        if not name or len(name) < 2:
            return jsonify({'success': False, 'message': 'Name must be at least 2 characters'}), 400
        
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        country = request.form.get('country', '').strip()
        
        # Update customer
        customer.name = name
        customer.phone = phone or None
        customer.address = address or None
        customer.city = city or None
        customer.country = country or None
        
        db.session.commit()
        
        session['customer_name'] = customer.name
        session.modified = True
        
        return jsonify({
            'success': True, 
            'message': 'Profile updated successfully! 🎉',
            'customer_name': customer.name
        }), 200
        
    except Exception as e:
        db.session.rollback()
        app_logger.log_error('ProfileUpdateError', str(e))
        return jsonify({
            'success': False, 
            'message': f'Error updating profile: {str(e)}'
        }), 500
