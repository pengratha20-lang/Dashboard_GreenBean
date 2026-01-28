from flask import render_template, request, redirect, url_for, Blueprint
from sqlalchemy import text
from functools import wraps
from werkzeug.security import generate_password_hash
import os
from upload_service import save_image
import config
from auth_helper import login_required

user_bp = Blueprint('user_module', __name__, url_prefix='')

UPLOAD_FOLDER = config.UPLOAD_FOLDER
ALLOWED_EXTENSIONS = config.ALLOWED_EXTENSIONS

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@user_bp.route('/users')
@login_required
def users_route():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    rows = getAllUsersList()
    total = len(rows)
    start = (page - 1) * per_page
    end = start + per_page
    users = rows[start:end]
    
    total_pages = (total + per_page - 1) // per_page
    
    return render_template('dashboard/user.html', module_name='Users', module_icon='fa-users', module='users', users=users, page=page, total_pages=total_pages, total=total)

@user_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    from app import db, User, app
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        profile_pic_file = request.files.get('profile_pic')
        
        if not all([username, password]):
            return redirect(url_for('user_module.add_user', message='Username and password are required', type='error'))
        
        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return redirect(url_for('user_module.add_user', message='Username already exists', type='error'))
        
        profile_pic_filename = handle_image_upload(profile_pic_file, app)

        new_user = User(
            username=username,
            password=generate_password_hash(password),
            profile_pic=profile_pic_filename or 'default.png'
        )
        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('user_module.users_route', message='User created successfully!', type='success'))
        except Exception as e:
            db.session.rollback()
            return redirect(url_for('user_module.add_user', message='Error adding user', type='error'))
    
    return render_template('dashboard/users_action/add_user.html', module_name='Add User', module_icon='fa-user-plus')

@user_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    from app import db, User, app
    
    user = User.query.get(user_id)
    
    if not user:
        return redirect(url_for('user_module.users_route'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username:
            return redirect(url_for('user_module.edit_user', user_id=user_id, message='Username is required', type='error'))
        
        # Check if username is already taken by another user
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != user_id:
            return redirect(url_for('user_module.edit_user', user_id=user_id, message='Username already exists', type='error'))
        
        user.username = username
        if password:
            user.password = generate_password_hash(password)
        
        profile_pic_file = request.files.get('profile_pic')
        if profile_pic_file and profile_pic_file.filename:
            delete_image_files(user.profile_pic)
            profile_pic_filename = handle_image_upload(profile_pic_file, app)
            if profile_pic_filename:
                user.profile_pic = profile_pic_filename
        
        try:
            db.session.commit()
            return redirect(url_for('user_module.users_route', message='User updated successfully!', type='success'))
        except Exception as e:
            db.session.rollback()
            return redirect(url_for('user_module.edit_user', user_id=user_id, message='Error updating user', type='error'))
    
    return render_template('dashboard/users_action/edit_user.html', user=user, module_name='Edit User', module_icon='fa-edit')

@user_bp.route('/users/delete/<int:user_id>', methods=['POST', 'GET'])
@login_required
def delete_user(user_id):
    from app import db, User
    
    user = User.query.get(user_id)
    
    if not user:
        return redirect(url_for('user_module.users_route'))
    
    delete_image_files(user.profile_pic)
    
    try:
        db.session.delete(user)
        db.session.commit()
        return redirect(url_for('user_module.users_route', message='User deleted successfully!', type='success'))
    except Exception as e:
        db.session.rollback()
        return redirect(url_for('user_module.users_route', message='Error deleting user', type='error'))

def getAllUsersList():
    from app import db
    sql = text("""SELECT id, username, profile_pic, created_at FROM user;""")
    result = db.session.execute(sql).fetchall()
    return [dict(row._mapping) for row in result]

def handle_image_upload(image_file, app):
    """Handle image upload and return filename or None""" 
    if not image_file or not image_file.filename or not allowed_file(image_file.filename):
        return None
    
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    try:
        images = save_image(image_file, app.config['UPLOAD_FOLDER'], app.config['ALLOWED_EXTENSIONS'])
        return images['original'] if isinstance(images, dict) else None
    except Exception as e:
        print(f"Image upload error: {e}")
        return None

def delete_image_files(image_filename):
    """Delete all image variants (original, resized, thumbnail)"""
    if not image_filename or image_filename == 'default.png':
        return
    
    name, ext = os.path.splitext(image_filename)
    for filename in [image_filename, f"resized_{name}{ext}", f"thumb_{name}{ext}"]:
        try:
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file {filename}: {e}")
