from flask import render_template, Blueprint
from auth_helper import login_required

# Create Blueprint
admin_bp = Blueprint('settings_module', __name__, url_prefix='')

@admin_bp.route('/settings')
@login_required
def settings_route():
    settings_data = {
        'store_name': 'Green Bean Admin',
        'email': 'admin@greenbean.com',
        'phone': '+1 (555) 123-4567',
        'address': '123 Plant Street, Garden City, ST 12345'
    }
    return render_template('dashboard/settings.html', settings=settings_data, module_name='Settings', module_icon='fa-cog')
