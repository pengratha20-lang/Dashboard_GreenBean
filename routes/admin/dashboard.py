from flask import render_template, jsonify, request, Blueprint
from auth_helper import login_required
import random

# Create Blueprint
dashboard_bp = Blueprint('admin', __name__, url_prefix='')

# ============ SAMPLE DATA GENERATION ============
def generate_chart_data(period='week'):
    """Generate dynamic chart data based on period"""
    if period == 'week':
        labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        revenue = [1200, 1900, 1500, 2200, 1800, 2500, 2800]
        orders = [45, 52, 48, 61, 55, 73, 82]
    elif period == 'month':
        labels = [f'Day {i}' for i in range(1, 31)]
        revenue = [random.randint(1000, 3000) for _ in range(30)]
        orders = [random.randint(30, 80) for _ in range(30)]
    elif period == 'quarter':
        labels = ['Month 1', 'Month 2', 'Month 3']
        revenue = [45000, 52000, 58000]
        orders = [1200, 1450, 1680]
    else:  # year
        labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        revenue = [25000, 28000, 32000, 35000, 38000, 42000, 45000, 48000, 52000, 55000, 58000, 62000]
        orders = [800, 920, 1050, 1180, 1320, 1450, 1600, 1750, 1920, 2050, 2180, 2350]
    
    return {
        'labels': labels,
        'revenue': revenue,
        'orders': orders
    }

def get_analytics_stats(period='week'):
    """Get analytics statistics based on period"""
    base_stats = {
        'week': {
            'revenue': '$12,450',
            'revenue_change': '15',
            'orders': '432',
            'orders_change': '8',
            'avg_order': '$28.81',
            'avg_order_change': '5',
            'conversion': '3.2%',
            'conversion_change': '0.5'
        },
        'month': {
            'revenue': '$52,340',
            'revenue_change': '22',
            'orders': '1,840',
            'orders_change': '14',
            'avg_order': '$28.44',
            'avg_order_change': '7',
            'conversion': '3.8%',
            'conversion_change': '1.2'
        },
        'year': {
            'revenue': '$485,200',
            'revenue_change': '35',
            'orders': '18,450',
            'orders_change': '28',
            'avg_order': '$26.30',
            'avg_order_change': '3',
            'conversion': '4.2%',
            'conversion_change': '2.1'
        }
    }
    return base_stats.get(period, base_stats['week'])

# ============ DASHBOARD ROUTE ============
@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def dashboard_route():
    stats = {
        'total_orders': '1,234',
        'total_revenue': '$45,320',
        'active_customers': '892',
        'products_in_stock': '156'
    }
    
    recent_orders = [
        {'id': '#12345', 'customer': 'John Doe', 'amount': '$45.99', 'status': 'completed', 'date': 'Dec 10, 2025'},
        {'id': '#12344', 'customer': 'Jane Smith', 'amount': '$120.50', 'status': 'pending', 'date': 'Dec 10, 2025'},
        {'id': '#12343', 'customer': 'Bob Johnson', 'amount': '$89.99', 'status': 'processing', 'date': 'Dec 9, 2025'},
    ]
    
    chart_data = generate_chart_data('week')
    
    return render_template('dashboard/dashboard.html', stats=stats, recent_orders=recent_orders, chart_data=chart_data, module_name='Dashboard', module_icon='fa-home')


# ============ API ROUTES FOR DYNAMIC DATA ============
@dashboard_bp.route('/api/analytics')
def get_analytics_api():
    """API endpoint for dynamic analytics data"""
    period = request.args.get('period', 'week')
    stats = get_analytics_stats(period)
    chart_data = generate_chart_data(period)
    return jsonify({
        'stats': stats,
        'chart_data': chart_data,
        'period': period
    })

