from flask import render_template, Blueprint
from auth_helper import login_required

# Create Blueprint
admin_bp = Blueprint('order_module', __name__, url_prefix='')

@admin_bp.route('/orders')
@login_required
def orders_route():
    orders_list = [
        {'id': '#12345', 'customer': 'John Doe', 'email': 'john@example.com', 'amount': '$45.99', 'status': 'completed', 'date': 'Dec 10, 2025', 'items': 3},
        {'id': '#12344', 'customer': 'Jane Smith', 'email': 'jane@example.com', 'amount': '$120.50', 'status': 'pending', 'date': 'Dec 10, 2025', 'items': 5},
        {'id': '#12343', 'customer': 'Bob Johnson', 'email': 'bob@example.com', 'amount': '$89.99', 'status': 'processing', 'date': 'Dec 9, 2025', 'items': 2},
        {'id': '#12342', 'customer': 'Alice Brown', 'email': 'alice@example.com', 'amount': '$156.75', 'status': 'completed', 'date': 'Dec 9, 2025', 'items': 7},
        {'id': '#12341', 'customer': 'Mike Wilson', 'email': 'mike@example.com', 'amount': '$78.25', 'status': 'pending', 'date': 'Dec 8, 2025', 'items': 4},
        {'id': '#12340', 'customer': 'Sarah Davis', 'email': 'sarah@example.com', 'amount': '$203.50', 'status': 'completed', 'date': 'Dec 8, 2025', 'items': 9},
    ]
    return render_template('dashboard/orders.html', orders=orders_list, module_name='Order Management', module_icon='fa-shopping-cart')
