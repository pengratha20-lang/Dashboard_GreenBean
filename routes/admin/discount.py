from flask import render_template, Blueprint
from auth_helper import login_required

# Create Blueprint
admin_bp = Blueprint('discount_module', __name__, url_prefix='')

@admin_bp.route('/discounts')
@login_required
def discounts_route():
    discounts_list = [
        {'id': 1, 'code': 'SAVE10', 'description': '10% off all plants', 'discount': '10%', 'expiry': 'Dec 31, 2025', 'status': 'active'},
        {'id': 2, 'code': 'NEWYEAR20', 'description': '20% off indoor plants', 'discount': '20%', 'expiry': 'Jan 15, 2026', 'status': 'active'},
        {'id': 3, 'code': 'HOLIDAY15', 'description': '15% off orders over $50', 'discount': '15%', 'expiry': 'Dec 25, 2025', 'status': 'inactive'},
    ]
    return render_template('dashboard/discounts.html', discounts=discounts_list, module_name='Discount Management', module_icon='fa-tag')
