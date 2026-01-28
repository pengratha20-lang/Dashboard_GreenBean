from flask import render_template, Blueprint
from auth_helper import login_required
from .dashboard import get_analytics_stats, generate_chart_data

# Create Blueprint
admin_bp = Blueprint('analytics_module', __name__, url_prefix='')

@admin_bp.route('/analytics')
@login_required
def analytics_route():
    period = 'week'
    stats = get_analytics_stats(period)
    chart_data = generate_chart_data(period)
    
    analytics_data = {
        'stats': stats,
        'chart_data': chart_data,
        'period': period,
        'categories': {
            'labels': ['Indoor Plants', 'Outdoor Plants', 'Accessories', 'Pots'],
            'data': [35, 25, 20, 20],
            'colors': ['#22a54a', '#1aa179', '#20c997', '#ff9800']
        },
        'top_products': {
            'labels': ['Snake Plant', 'Monstera', 'Golden Pothos', 'ZZ Plant', 'Lucky Bamboo'],
            'data': [125, 98, 87, 76, 65]
        },
        'customers_growth': {
            'labels': ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5'],
            'data': [45, 52, 48, 61, 75]
        }
    }
    
    return render_template('dashboard/analytics.html', analytics=analytics_data, module_name='Analytics & Reports', module_icon='fa-chart-line')
