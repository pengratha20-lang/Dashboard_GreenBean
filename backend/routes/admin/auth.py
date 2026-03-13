from flask import render_template, request, redirect, url_for, session, Blueprint
from werkzeug.security import check_password_hash, generate_password_hash
from database import db

auth_bp = Blueprint('auth', __name__, url_prefix='')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        from model.user import User
        
        # Accept either username or email
        login_input = request.form.get('login')
        password = request.form.get('password')
        
        # Validate input
        if not login_input or not password:
            return redirect(url_for('auth.login', 
                                  message='Please fill in all fields', 
                                  type='error'))
        
        try:
            # Find user by username or email
            user = User.query.filter(
                (User.username == login_input) | (User.email == login_input)
            ).first()
            
            if user and check_password_hash(user.password, password):
                # Create session
                session['user_id'] = user.id
                session['username'] = user.username
                session['email'] = user.email
                session['profile_pic'] = user.profile_pic
                session.permanent = True
                
                return redirect(url_for('admin.dashboard_route'))
            else:
                return redirect(url_for('auth.login', 
                                      message='Invalid username/email or password', 
                                      type='error'))
        except Exception as e:
            return redirect(url_for('auth.login', 
                                  message='Database error: ' + str(e), 
                                  type='error'))
    
    return render_template('dashboard/login.html')
