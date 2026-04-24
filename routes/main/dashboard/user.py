from flask import render_template, request, redirect, url_for, Blueprint, session
from sqlalchemy import text
from werkzeug.security import generate_password_hash
from core.database import db
from model.user import User
import os
from core.upload_service_enhanced import save_image_organized
from config.settings import ALLOWED_EXTENSIONS, UPLOAD_FOLDER
from core.auth_helper import login_required

user_bp = Blueprint('user_module', __name__, url_prefix='')

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

    return render_template('dashboard/user.html',
                           module_name='Users', module_icon='fa-users',
                           module='users', users=users,
                           page=page, total_pages=total_pages, total=total)

@user_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        profile_pic_file = request.files.get('profile_pic')

        if not all([username, email, password]):
            return redirect(url_for('user_module.add_user',
                                    message='Username, email and password are required', type='error'))

        if '@' not in email or '.' not in email:
            return redirect(url_for('user_module.add_user',
                                    message='Please enter a valid email address', type='error'))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return redirect(url_for('user_module.add_user',
                                    message='Username already exists', type='error'))

        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            return redirect(url_for('user_module.add_user',
                                    message='Email already registered', type='error'))

        profile_pic_filename = handle_image_upload(profile_pic_file)

        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            profile_pic=profile_pic_filename or 'default.png'
        )
        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('user_module.users_route',
                                    message='User created successfully!', type='success'))
        except Exception as e:
            db.session.rollback()
            return redirect(url_for('user_module.add_user',
                                    message='Error adding user: ' + str(e), type='error'))

    return render_template('dashboard/users_action/add_user.html',
                           module_name='Add User', module_icon='fa-user-plus')

@user_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    user = User.query.get(user_id)

    if not user:
        return redirect(url_for('user_module.users_route'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if not username or not email:
            return redirect(url_for('user_module.edit_user',
                                    user_id=user_id,
                                    message='Username and email are required', type='error'))

        if '@' not in email or '.' not in email:
            return redirect(url_for('user_module.edit_user',
                                    user_id=user_id,
                                    message='Please enter a valid email address', type='error'))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != user_id:
            return redirect(url_for('user_module.edit_user',
                                    user_id=user_id,
                                    message='Username already exists', type='error'))

        existing_email = User.query.filter_by(email=email).first()
        if existing_email and existing_email.id != user_id:
            return redirect(url_for('user_module.edit_user',
                                    user_id=user_id,
                                    message='Email already registered', type='error'))

        user.username = username
        user.email = email
        if password:
            user.password = generate_password_hash(password)

        profile_pic_file = request.files.get('profile_pic')
        if profile_pic_file and profile_pic_file.filename:
            delete_image_files(user.profile_pic)
            profile_pic_filename = handle_image_upload(profile_pic_file)
            if profile_pic_filename:
                user.profile_pic = profile_pic_filename

        try:
            db.session.commit()
            return redirect(url_for('user_module.users_route',
                                    message='User updated successfully!', type='success'))
        except Exception as e:
            db.session.rollback()
            return redirect(url_for('user_module.edit_user',
                                    user_id=user_id,
                                    message='Error updating user: ' + str(e), type='error'))

    return render_template('dashboard/users_action/edit_user.html',
                           user=user, module_name='Edit User', module_icon='fa-edit')

@user_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get(user_id)

    if not user:
        return redirect(url_for('user_module.users_route'))

    if session.get('admin_user_id') == user_id:
        return redirect(url_for('user_module.users_route',
                                message='You cannot delete the currently logged-in administrator.',
                                type='error'))

    delete_image_files(user.profile_pic)

    try:
        db.session.delete(user)
        db.session.commit()
        return redirect(url_for('user_module.users_route',
                                message='User deleted successfully!', type='success'))
    except Exception as e:
        db.session.rollback()
        return redirect(url_for('user_module.users_route',
                                message='Error deleting user', type='error'))

def getAllUsersList():
    sql = text("""SELECT id, username, email, profile_pic, created_at FROM user;""")
    result = db.session.execute(sql).fetchall()
    return [dict(row._mapping) for row in result]

def handle_image_upload(image_file):
    """Handle image upload and return filename or None"""
    if not image_file or not image_file.filename or not allowed_file(image_file.filename):
        return None
    try:
        result = save_image_organized(image_file, 'user')
        if isinstance(result, dict):
            return result.get('original')
        return None
    except Exception as e:
        print(f"Image upload error: {e}")
        return None

def delete_image_files(image_filename):
    """Delete all image variants from organized structure"""
    if not image_filename or image_filename == 'default.png':
        return
    from core.image_helper import ImagePathHelper
    try:
        ImagePathHelper.delete_all_versions('user', image_filename)
    except Exception as e:
        print(f"Could not delete image variants for {image_filename}: {e}")
