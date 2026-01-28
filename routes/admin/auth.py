from flask import render_template, request, redirect, url_for, session, Blueprint
from werkzeug.security import check_password_hash, generate_password_hash
from database import db

auth_bp = Blueprint('auth', __name__, url_prefix='')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        from model.user import User
        
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Validate input
        if not username or not password:
            return redirect(url_for('auth.login', 
                                  message='Please fill in all fields', 
                                  type='error'))
        
        try:
            # Find user in database
            user = User.query.filter_by(username=username).first()
            
            if user and check_password_hash(user.password, password):
                # Create session
                session['user_id'] = user.id
                session['username'] = user.username
                session['profile_pic'] = user.profile_pic
                session.permanent = True
                
                return redirect(url_for('admin.dashboard_route'))
            else:
                return redirect(url_for('auth.login', 
                                      message='Invalid username or password', 
                                      type='error'))
        except Exception as e:
            return redirect(url_for('auth.login', 
                                  message='Database error: ' + str(e), 
                                  type='error'))
    
    return render_template('dashboard/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        from model.user import User
        
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate input
        if not username or not password or not confirm_password:
            return redirect(url_for('auth.register', 
                                  message='Please fill in all fields', 
                                  type='error'))
        
        if password != confirm_password:
            return redirect(url_for('auth.register', 
                                  message='Passwords do not match', 
                                  type='error'))
        
        try:
            # Check if user already exists
            if User.query.filter_by(username=username).first():
                return redirect(url_for('auth.register', 
                                      message='Username already exists', 
                                      type='error'))
            
            # Create new user
            new_user = User(
                username=username,
                password=generate_password_hash(password),
                profile_pic='default.png'
            )
            db.session.add(new_user)
            db.session.commit()
            
            return redirect(url_for('auth.login', 
                                  message='Registration successful! Please log in.', 
                                  type='success'))
        except Exception as e:
            db.session.rollback()
            return redirect(url_for('auth.register', 
                                  message='An error occurred during registration: ' + str(e), 
                                  type='error'))
    
    return render_template('dashboard/register.html')
