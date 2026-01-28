from flask import render_template, Blueprint
from auth_helper import login_required

# Create Blueprint
admin_bp = Blueprint('customer_module', __name__, url_prefix='')

@admin_bp.route('/customers')
@login_required
def customers_route():
    customers_list = [
        {'id': 1, 'name': 'John Doe', 'email': 'john@example.com', 'phone': '555-0123', 'total_orders': 5, 'join_date': 'Nov 2024'},
        {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com', 'phone': '555-0124', 'total_orders': 8, 'join_date': 'Oct 2024'},
        {'id': 3, 'name': 'Bob Johnson', 'email': 'bob@example.com', 'phone': '555-0125', 'total_orders': 3, 'join_date': 'Dec 2024'},
    ]
    return render_template('dashboard/customers.html', customers=customers_list, module_name='Customer Management', module_icon='fa-users')
