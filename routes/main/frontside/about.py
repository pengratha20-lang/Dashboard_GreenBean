from flask import Blueprint, render_template

about_bp = Blueprint('about', __name__)

@about_bp.route('/about')
def about():
    # Render dedicated about page
    return render_template('frontside/home/about.html', title="Green Garden - About Us")
