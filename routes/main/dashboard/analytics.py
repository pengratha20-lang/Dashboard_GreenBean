from datetime import datetime, time, timedelta

from flask import Blueprint, jsonify, render_template, request
from sqlalchemy import func, text

from core.auth_helper import login_required
from core.database import db
from model.customer import Customer
from model.order import Order

# Create Blueprint
analytics_bp = Blueprint('analytics_module', __name__, url_prefix='')


def _safe_pct_change(current, previous):
    if previous in (None, 0):
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100, 1)


def _period_config(period):
    return {
        'week': {'days': 7, 'label': 'week'},
        'month': {'days': 30, 'label': 'month'},
        'year': {'days': 365, 'label': 'year'},
    }.get(period, {'days': 7, 'label': 'week'})


def _period_bounds(period):
    config = _period_config(period)
    now = datetime.now()
    current_end = now
    current_start_date = (now - timedelta(days=config['days'] - 1)).date()
    current_start = datetime.combine(current_start_date, time.min)

    previous_end = current_start - timedelta(microseconds=1)
    previous_start = previous_end - timedelta(days=config['days'] - 1)
    previous_start = datetime.combine(previous_start.date(), time.min)

    return {
        'period': config['label'],
        'current_start': current_start,
        'current_end': current_end,
        'previous_start': previous_start,
        'previous_end': previous_end,
    }


def _custom_bounds(start_date_str=None, end_date_str=None):
    if not start_date_str or not end_date_str:
        return None

    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    if end_date < start_date:
        raise ValueError('End date must be on or after start date')

    days = (end_date - start_date).days + 1
    current_start = datetime.combine(start_date, time.min)
    current_end = datetime.combine(end_date, time.max)
    previous_end = current_start - timedelta(microseconds=1)
    previous_start = datetime.combine((previous_end.date() - timedelta(days=days - 1)), time.min)

    return {
        'period': 'custom',
        'current_start': current_start,
        'current_end': current_end,
        'previous_start': previous_start,
        'previous_end': previous_end,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'days': days,
    }


def _resolve_bounds(period='week', start_date=None, end_date=None):
    custom = _custom_bounds(start_date, end_date)
    if custom:
        return custom

    bounds = _period_bounds(period)
    bounds['start_date'] = bounds['current_start'].date().isoformat()
    bounds['end_date'] = bounds['current_end'].date().isoformat()
    bounds['days'] = (bounds['current_end'].date() - bounds['current_start'].date()).days + 1
    return bounds


def _month_points(count=12):
    today = datetime.now().date().replace(day=1)
    points = []
    year = today.year
    month = today.month

    for offset in range(count - 1, -1, -1):
        m = month - offset
        y = year
        while m <= 0:
            m += 12
            y -= 1
        points.append({
            'key': f'{y:04d}-{m:02d}',
            'label': datetime(y, m, 1).strftime('%b %Y'),
            'date': datetime(y, m, 1).date()
        })
    return points


def _day_points(days, end_date=None):
    today = end_date or datetime.now().date()
    points = []
    for offset in range(days - 1, -1, -1):
        point_date = today - timedelta(days=offset)
        points.append({
            'key': point_date.isoformat(),
            'label': point_date.strftime('%a' if days == 7 else '%d %b'),
            'date': point_date
        })
    return points


def get_real_analytics_stats(period='week', start_date=None, end_date=None):
    """Get period-aware analytics statistics with real comparisons."""
    bounds = _resolve_bounds(period, start_date, end_date)
    current_start = bounds['current_start']
    current_end = bounds['current_end']
    previous_start = bounds['previous_start']
    previous_end = bounds['previous_end']

    try:
        current_revenue = db.session.query(func.sum(Order.total_amount)).filter(
            Order.status == 'completed',
            Order.created_at >= current_start,
            Order.created_at <= current_end
        ).scalar() or 0
        previous_revenue = db.session.query(func.sum(Order.total_amount)).filter(
            Order.status == 'completed',
            Order.created_at >= previous_start,
            Order.created_at <= previous_end
        ).scalar() or 0

        current_orders = Order.query.filter(
            Order.status == 'completed',
            Order.created_at >= current_start,
            Order.created_at <= current_end
        ).count()
        previous_orders = Order.query.filter(
            Order.status == 'completed',
            Order.created_at >= previous_start,
            Order.created_at <= previous_end
        ).count()

        current_avg_order = db.session.query(func.avg(Order.total_amount)).filter(
            Order.status == 'completed',
            Order.created_at >= current_start,
            Order.created_at <= current_end
        ).scalar() or 0
        previous_avg_order = db.session.query(func.avg(Order.total_amount)).filter(
            Order.status == 'completed',
            Order.created_at >= previous_start,
            Order.created_at <= previous_end
        ).scalar() or 0

        current_customers = Customer.query.filter(
            Customer.created_at >= current_start,
            Customer.created_at <= current_end
        ).count()
        previous_customers = Customer.query.filter(
            Customer.created_at >= previous_start,
            Customer.created_at <= previous_end
        ).count()

        return {
            'revenue': f'${current_revenue:,.2f}',
            'revenue_value': round(float(current_revenue), 2),
            'revenue_change': _safe_pct_change(current_revenue, previous_revenue),
            'orders': str(current_orders),
            'orders_value': current_orders,
            'orders_change': _safe_pct_change(current_orders, previous_orders),
            'avg_order': f'${current_avg_order:,.2f}',
            'avg_order_value': round(float(current_avg_order), 2),
            'avg_order_change': _safe_pct_change(current_avg_order, previous_avg_order),
            'customers': str(current_customers),
            'customers_value': current_customers,
            'customers_change': _safe_pct_change(current_customers, previous_customers),
        }
    except Exception:
        return {
            'revenue': '$0.00',
            'revenue_value': 0,
            'revenue_change': 0,
            'orders': '0',
            'orders_value': 0,
            'orders_change': 0,
            'avg_order': '$0.00',
            'avg_order_value': 0,
            'avg_order_change': 0,
            'customers': '0',
            'customers_value': 0,
            'customers_change': 0,
        }


def get_real_chart_data(period='week', start_date=None, end_date=None):
    """Get real revenue and order trend data from database."""
    try:
        bounds = _resolve_bounds(period, start_date, end_date)
        if bounds['period'] == 'year':
            points = _month_points(12)
            start_date = points[0]['date']
            grouped = db.session.query(
                func.strftime('%Y-%m', Order.created_at).label('period_key'),
                func.count(Order.id).label('count'),
                func.sum(Order.total_amount).label('revenue')
            ).filter(
                Order.status == 'completed',
                Order.created_at >= datetime.combine(start_date, time.min)
            ).group_by(func.strftime('%Y-%m', Order.created_at)).all()
        else:
            days = bounds['days']
            points = _day_points(days, bounds['current_end'].date())
            start_date = points[0]['date']
            grouped = db.session.query(
                func.date(Order.created_at).label('period_key'),
                func.count(Order.id).label('count'),
                func.sum(Order.total_amount).label('revenue')
            ).filter(
                Order.status == 'completed',
                Order.created_at >= datetime.combine(start_date, time.min)
            ).group_by(func.date(Order.created_at)).all()

        grouped_map = {str(row.period_key): row for row in grouped}
        labels = [point['label'] for point in points]
        orders = [int(grouped_map.get(point['key']).count) if grouped_map.get(point['key']) else 0 for point in points]
        revenue = [round(float(grouped_map.get(point['key']).revenue or 0), 2) if grouped_map.get(point['key']) else 0 for point in points]

        return {
            'labels': labels,
            'orders': orders,
            'revenue': revenue
        }
    except Exception:
        return {
            'labels': ['No Data'],
            'orders': [0],
            'revenue': [0]
        }


def get_top_products(period='week', start_date=None, end_date=None):
    """Get top selling products by quantity for the selected period."""
    bounds = _resolve_bounds(period, start_date, end_date)
    try:
        result = db.session.execute(text('''
            SELECT p.product_name, COALESCE(SUM(oi.quantity), 0) AS units_sold
            FROM product p
            LEFT JOIN order_item oi ON p.id = oi.product_id
            LEFT JOIN "order" o ON o.id = oi.order_id
            WHERE o.id IS NULL OR (
                o.created_at >= :start_date
                AND o.created_at <= :end_date
                AND o.status = 'completed'
            )
            GROUP BY p.id, p.product_name
            ORDER BY units_sold DESC, p.product_name ASC
            LIMIT 5
        '''), {
            'start_date': bounds['current_start'],
            'end_date': bounds['current_end'],
        }).fetchall()

        labels = [row[0] for row in result if row[1] and row[1] > 0]
        data = [int(row[1]) for row in result if row[1] and row[1] > 0]

        if not labels:
            labels = ['No Products']
            data = [0]

        return {'labels': labels, 'data': data}
    except Exception:
        return {'labels': ['No Products'], 'data': [0]}


def get_category_stats(period='week', start_date=None, end_date=None):
    """Get sales value by category for the selected period."""
    bounds = _resolve_bounds(period, start_date, end_date)
    try:
        result = db.session.execute(text('''
            SELECT
                c.category_name,
                COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS revenue
            FROM category c
            LEFT JOIN product p ON c.id = p.category_id
            LEFT JOIN order_item oi ON p.id = oi.product_id
            LEFT JOIN "order" o ON o.id = oi.order_id
            AND o.created_at >= :start_date
            AND o.created_at <= :end_date
            AND o.status = 'completed'
            GROUP BY c.id, c.category_name
            ORDER BY revenue DESC, c.category_name ASC
        '''), {
            'start_date': bounds['current_start'],
            'end_date': bounds['current_end'],
        }).fetchall()

        labels = [row[0] for row in result if float(row[1] or 0) > 0]
        data = [round(float(row[1] or 0), 2) for row in result if float(row[1] or 0) > 0]
        colors = ['#22a54a', '#1aa179', '#20c997', '#ff9800', '#f44336', '#2196f3']

        if not labels:
            labels = ['No Category Sales']
            data = [0]
            colors = ['#cbd5e1']

        return {
            'labels': labels,
            'data': data,
            'colors': colors[:len(labels)]
        }
    except Exception:
        return {
            'labels': ['No Category Sales'],
            'data': [0],
            'colors': ['#cbd5e1']
        }


def get_payment_method_stats(period='week', start_date=None, end_date=None):
    bounds = _resolve_bounds(period, start_date, end_date)
    try:
        result = db.session.query(
            Order.payment_method,
            func.count(Order.id).label('total')
        ).filter(
            Order.created_at >= bounds['current_start'],
            Order.created_at <= bounds['current_end']
        ).group_by(Order.payment_method).all()

        labels = [str(row.payment_method or 'unknown').replace('_', ' ').title() for row in result]
        data = [int(row.total) for row in result]

        if not labels:
            labels = ['No Orders']
            data = [0]

        return {
            'labels': labels,
            'data': data,
            'colors': ['#22a54a', '#0ea5e9', '#f59e0b', '#8b5cf6'][:len(labels)]
        }
    except Exception:
        return {
            'labels': ['No Orders'],
            'data': [0],
            'colors': ['#cbd5e1']
        }


def get_order_status_stats(period='week', start_date=None, end_date=None):
    bounds = _resolve_bounds(period, start_date, end_date)
    try:
        result = db.session.query(
            Order.status,
            func.count(Order.id).label('total')
        ).filter(
            Order.created_at >= bounds['current_start'],
            Order.created_at <= bounds['current_end']
        ).group_by(Order.status).all()

        labels = [str(row.status or 'unknown').replace('_', ' ').title() for row in result]
        data = [int(row.total) for row in result]

        if not labels:
            labels = ['No Orders']
            data = [0]

        return {
            'labels': labels,
            'data': data,
            'colors': ['#f59e0b', '#22a54a', '#ef4444', '#0ea5e9', '#8b5cf6'][:len(labels)]
        }
    except Exception:
        return {
            'labels': ['No Orders'],
            'data': [0],
            'colors': ['#cbd5e1']
        }


def build_analytics_payload(period='week', start_date=None, end_date=None):
    bounds = _resolve_bounds(period, start_date, end_date)
    return {
        'stats': get_real_analytics_stats(period, start_date, end_date),
        'chart_data': get_real_chart_data(period, start_date, end_date),
        'period': bounds['period'],
        'selected_range': {
            'start_date': bounds['start_date'],
            'end_date': bounds['end_date'],
        },
        'categories': get_category_stats(period, start_date, end_date),
        'top_products': get_top_products(period, start_date, end_date),
        'payment_methods': get_payment_method_stats(period, start_date, end_date),
        'order_statuses': get_order_status_stats(period, start_date, end_date),
        'last_updated': datetime.now().strftime('%b %d, %Y %I:%M %p'),
    }


@analytics_bp.route('/analytics')
@login_required
def analytics_route():
    analytics_data = build_analytics_payload('week')
    return render_template(
        'dashboard/analytics.html',
        analytics=analytics_data,
        module_name='Analytics & Reports',
        module_icon='fa-chart-line'
    )


@analytics_bp.route('/api/analytics', methods=['GET'])
@login_required
def get_analytics_api():
    period = request.args.get('period', 'week')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    try:
        return jsonify(build_analytics_payload(period, start_date, end_date))
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
