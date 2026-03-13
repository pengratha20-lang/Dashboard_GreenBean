from flask import render_template, jsonify, request, Blueprint
from auth_helper import login_required
from database import db
from model.order import Order
from model.customer import Customer
from model.user import User
from datetime import datetime, timedelta
from sqlalchemy import func
import random

# Create Blueprint
dashboard_bp = Blueprint('admin', __name__, url_prefix='')

# ============ REAL DATA FUNCTIONS ============
def get_real_stats():
    """Get real statistics from database"""
    try:
        total_orders = Order.query.count()
        total_revenue = db.session.query(func.sum(Order.total_amount)).filter(
            Order.status == 'completed'
        ).scalar() or 0
        total_customers = Customer.query.count()
        total_users = User.query.count()
        
        # Get product count from database
        from sqlalchemy import text
        product_count = db.session.execute(text('SELECT COUNT(*) FROM product')).scalar() or 0
        
        return {
            'total_orders': str(total_orders),
            'total_revenue': f'${total_revenue:,.2f}',
            'active_customers': str(total_customers),
            'products_in_stock': str(product_count)
        }
    except Exception as e:
        return {
            'total_orders': '0',
            'total_revenue': '$0',
            'active_customers': '0',
            'products_in_stock': '0'
        }

def get_real_recent_orders(limit=5):
    """Get recent orders from database"""
    try:
        orders = Order.query.order_by(Order.created_at.desc()).limit(limit).all()
        result = []
        for order in orders:
            result.append({
                'id': order.order_number,
                'customer': order.customer.name if order.customer else 'Unknown',
                'amount': f'${order.total_amount:.2f}',
                'status': order.status.capitalize(),
                'date': order.created_at.strftime('%b %d, %Y') if order.created_at else 'N/A'
            })
        return result
    except Exception as e:
        return []

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
    stats = get_real_stats()
    recent_orders = get_real_recent_orders(5)
    chart_data = generate_chart_data('week')
    
    return render_template('dashboard/dashboard.html', stats=stats, recent_orders=recent_orders, chart_data=chart_data, module_name='Dashboard', module_icon='fa-home')


# ============ API ROUTES FOR DYNAMIC DATA ============
@dashboard_bp.route('/api/analytics')
@login_required
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


@dashboard_bp.route('/api/dashboard-stats')
@login_required
def get_dashboard_stats_api():
    """API endpoint for dashboard stats"""
    stats = get_real_stats()
    recent_orders = get_real_recent_orders(5)
    return jsonify({
        'stats': stats,
        'recent_orders': recent_orders
    })

