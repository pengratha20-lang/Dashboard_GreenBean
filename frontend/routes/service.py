from flask import Blueprint, redirect, url_for

service_bp = Blueprint('service', __name__)

@service_bp.route('/service')
@service_bp.route('/services')
def service():
    # Redirect to homepage services section instead of separate page
    return redirect(url_for('home.home') + '#services')
