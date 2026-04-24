"""
Global search functionality - Search across all modules
"""
from flask import Blueprint, request, jsonify
from core.auth_helper import login_required
from model.product import Product
from model.customer import Customer
from model.order import Order
from model.category import Category
from model.discount import Discount

search_bp = Blueprint('search_module', __name__, url_prefix='/api/search')

@search_bp.route('/global', methods=['POST'])
@login_required
def global_search():
    """Global search across all entities"""
    try:
        search_term = request.json.get('q', '').strip().lower()
        limit = request.json.get('limit', 50)
        
        if not search_term or len(search_term) < 2:
            return jsonify({'success': False, 'error': 'Search term must be at least 2 characters'}), 400
        
        results = {
            'products': [],
            'customers': [],
            'orders': [],
            'categories': [],
            'discounts': []
        }
        
        # Search products
        products = Product.query.filter(
            Product.product_name.ilike(f'%{search_term}%')
        ).limit(limit).all()
        for p in products:
            results['products'].append({
                'id': p.id,
                'name': p.product_name,
                'type': 'product',
                'price': f'${p.price:.2f}',
                'stock': p.stock,
                'url': f'/products/edit/{p.id}'
            })
        
        # Search customers
        customers = Customer.query.filter(
            (Customer.name.ilike(f'%{search_term}%')) |
            (Customer.email.ilike(f'%{search_term}%'))
        ).limit(limit).all()
        for c in customers:
            results['customers'].append({
                'id': c.id,
                'name': c.name,
                'type': 'customer',
                'email': c.email,
                'phone': c.phone_number,
                'url': f'/customers/edit/{c.id}'
            })
        
        # Search orders
        orders = Order.query.filter(
            Order.order_number.ilike(f'%{search_term}%')
        ).limit(limit).all()
        for o in orders:
            results['orders'].append({
                'id': o.id,
                'name': f"Order {o.order_number}",
                'type': 'order',
                'status': o.status,
                'total': f'${o.total_amount:.2f}',
                'url': f'/orders/edit/{o.id}'
            })
        
        # Search categories
        categories = Category.query.filter(
            Category.category_name.ilike(f'%{search_term}%')
        ).limit(limit).all()
        for cat in categories:
            results['categories'].append({
                'id': cat.id,
                'name': cat.category_name,
                'type': 'category',
                'icon': cat.icon,
                'url': f'/categories/edit/{cat.id}'
            })
        
        # Search discounts
        discounts = Discount.query.filter(
            (Discount.code.ilike(f'%{search_term}%')) |
            (Discount.description.ilike(f'%{search_term}%'))
        ).limit(limit).all()
        for d in discounts:
            results['discounts'].append({
                'id': d.id,
                'name': d.code,
                'type': 'discount',
                'description': d.description[:50] if d.description else '',
                'discount': f'{d.discount_percent}%' if d.discount_percent else f'${d.discount_amount:.2f}',
                'url': f'/discounts/edit/{d.id}'
            })
        
        # Calculate total results
        total_results = sum(len(v) for v in results.values() if isinstance(v, list))
        
        return jsonify({
            'success': True,
            'results': results,
            'total': total_results,
            'search_term': search_term
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@search_bp.route('/products', methods=['GET'])
@login_required
def search_products():
    """Search products"""
    try:
        search_term = request.args.get('q', '').strip().lower()
        
        if not search_term:
            return jsonify({'success': False, 'results': []}), 400
        
        products = Product.query.filter(
            Product.product_name.ilike(f'%{search_term}%')
        ).limit(20).all()
        
        results = [{
            'id': p.id,
            'name': p.product_name,
            'price': f'${p.price:.2f}',
            'stock': p.stock
        } for p in products]
        
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@search_bp.route('/customers', methods=['GET'])
@login_required
def search_customers():
    """Search customers"""
    try:
        search_term = request.args.get('q', '').strip().lower()
        
        if not search_term:
            return jsonify({'success': False, 'results': []}), 400
        
        customers = Customer.query.filter(
            (Customer.name.ilike(f'%{search_term}%')) |
            (Customer.email.ilike(f'%{search_term}%'))
        ).limit(20).all()
        
        results = [{
            'id': c.id,
            'name': c.name,
            'email': c.email,
            'phone': c.phone_number
        } for c in customers]
        
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
