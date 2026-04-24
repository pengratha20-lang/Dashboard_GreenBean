from flask import render_template, jsonify, request, Blueprint
from core.auth_helper import login_required
from core.database import db
from model.order import Order
from model.customer import Customer
from model.user import User
from routes.main.dashboard.analytics import build_analytics_payload
from sqlalchemy import func

# Create Blueprint
dashboard_bp = Blueprint('admin', __name__, url_prefix='')

# ============ REAL DATA FUNCTIONS ============
def get_real_stats():
    """Get real statistics from database"""
    try:
        total_orders = Order.query.filter(Order.status == 'completed').count()
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
            'total_orders_value': total_orders,
            'total_revenue': f'${total_revenue:,.2f}',
            'total_revenue_value': round(float(total_revenue), 2),
            'active_customers': str(total_customers),
            'active_customers_value': total_customers,
            'products_in_stock': str(product_count),
            'products_in_stock_value': product_count
        }
    except Exception:
        return {
            'total_orders': '0',
            'total_orders_value': 0,
            'total_revenue': '$0',
            'total_revenue_value': 0,
            'active_customers': '0',
            'active_customers_value': 0,
            'products_in_stock': '0',
            'products_in_stock_value': 0
        }

def get_real_recent_orders(limit=5):
    """Get recent orders from database"""
    try:
        from sqlalchemy.orm import joinedload
        orders = Order.query.options(
            joinedload(Order.customer)
        ).order_by(Order.created_at.desc()).limit(limit).all()
        result = []
        for order in orders:
            customer_name = order.customer.name if order.customer else 'Guest checkout'
            result.append({
                'id': order.order_number,
                'customer': customer_name,
                'avatar_letter': customer_name[0].upper() if customer_name else 'G',
                'amount': f'{order.currency or "USD"} {order.total_amount:,.2f}' if (order.currency or 'USD') == 'KHR' else f'${order.total_amount:,.2f}',
                'amount_value': round(float(order.total_amount), 2),
                'currency': order.currency or 'USD',
                'status': order.status.capitalize(),
                'date': order.created_at.strftime('%b %d, %Y') if order.created_at else 'N/A'
            })
        return result
    except Exception:
        return []

# ============ DASHBOARD ROUTE ============
@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def dashboard_route():
    stats = get_real_stats()
    recent_orders = get_real_recent_orders(5)
    analytics = build_analytics_payload('week')
    
    return render_template(
        'dashboard/dashboard.html',
        stats=stats,
        recent_orders=recent_orders,
        chart_data=analytics['chart_data'],
        dashboard_analytics=analytics,
        module_name='Dashboard',
        module_icon='fa-home'
    )


# ============ API ROUTES FOR DYNAMIC DATA ============
@dashboard_bp.route('/api/dashboard-analytics')
@login_required
def get_dashboard_analytics_api():
    """API endpoint for dashboard-specific chart data"""
    period = request.args.get('period', 'week')
    return jsonify(build_analytics_payload(period))


@dashboard_bp.route('/api/dashboard-stats')
@login_required
def get_dashboard_stats_api():
    """API endpoint for dashboard stats"""
    stats = get_real_stats()
    recent_orders = get_real_recent_orders(5)
    analytics = build_analytics_payload('week')
    return jsonify({
        'stats': stats,
        'recent_orders': recent_orders,
        'analytics': analytics
    })

