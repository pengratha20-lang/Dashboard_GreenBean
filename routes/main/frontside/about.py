from flask import Blueprint, redirect, url_for

about_bp = Blueprint('about', __name__)

@about_bp.route('/about')
def about():
    # Redirect to homepage about section instead of separate page
    return redirect(url_for('home.home') + '#about')
