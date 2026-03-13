from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from model.customer import Customer
from database import db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle customer login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Email and password are required.', 'danger')
            return redirect(url_for('auth.login'))
        
        try:
            customer = Customer.query.filter_by(email=email).first()
            
            if customer and check_password_hash(customer.password, password):
                # Store customer info in session
                session['user_id'] = customer.id
                session['user_name'] = customer.name
                session['user_email'] = customer.email
                session.modified = True
                
                flash(f'Welcome back, {customer.name}!', 'success')
                return redirect(request.args.get('next') or url_for('home.home'))
            else:
                flash('Invalid email or password.', 'danger')
        except Exception as e:
            flash(f'Login error: {str(e)}', 'danger')
    
    return render_template('auth/login.html', title='Green Bean - Login')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle customer registration"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not all([name, email, password, confirm_password]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('auth.register'))
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.register'))
        
        try:
            # Check if email already exists
            existing_customer = Customer.query.filter_by(email=email).first()
            if existing_customer:
                flash('Email already registered. Please login or use a different email.', 'warning')
                return redirect(url_for('auth.login'))
            
            # Create new customer
            hashed_password = generate_password_hash(password)
            new_customer = Customer(
                name=name,
                email=email,
                password=hashed_password
            )
            
            db.session.add(new_customer)
            db.session.commit()
            
            # Auto login after registration
            session['user_id'] = new_customer.id
            session['user_name'] = new_customer.name
            session['user_email'] = new_customer.email
            session.modified = True
            
            flash('Registration successful! Welcome to Green Bean!', 'success')
            return redirect(url_for('home.home'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Registration error: {str(e)}', 'danger')
    
    return render_template('auth/register.html', title='Green Bean - Register')


@auth_bp.route('/logout')
def logout():
    """Handle customer logout"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home.home'))


@auth_bp.route('/profile')
def profile():
    """View and edit customer profile"""
    if 'user_id' not in session:
        flash('Please login first.', 'warning')
        return redirect(url_for('auth.login', next=url_for('auth.profile')))
    
    try:
        customer = Customer.query.get(session['user_id'])
        if not customer:
            session.clear()
            flash('Session expired. Please login again.', 'warning')
            return redirect(url_for('auth.login'))
        
        return render_template('auth/profile.html', title='My Account - Green Bean', customer=customer)
    except Exception as e:
        flash(f'Error loading profile: {str(e)}', 'danger')
        return redirect(url_for('home.home'))


@auth_bp.route('/profile/update', methods=['POST'])
def update_profile():
    """Update customer profile information"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    try:
        customer = Customer.query.get(session['user_id'])
        if not customer:
            return jsonify({'success': False, 'message': 'Customer not found'}), 404
        
        # Update fields
        customer.name = request.form.get('name', customer.name)
        customer.phone = request.form.get('phone', customer.phone)
        customer.address = request.form.get('address', customer.address)
        customer.city = request.form.get('city', customer.city)
        customer.country = request.form.get('country', customer.country)
        
        db.session.commit()
        
        # Update session
        session['user_name'] = customer.name
        session.modified = True
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.profile'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating profile: {str(e)}', 'danger')
        return redirect(url_for('auth.profile'))
