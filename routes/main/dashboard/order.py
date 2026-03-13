from flask import render_template, request, jsonify, Blueprint
from database import db
from auth_helper import login_required
from model.order import Order, OrderItem
from model.customer import Customer
from model.discount import Discount
from datetime import datetime
from services.main.dashboard.coupons import increment_global_usage_if_completed

# Create Blueprint
admin_bp = Blueprint('order_module', __name__, url_prefix='')

@admin_bp.route('/orders')
@login_required
def orders_route():
    orders = Order.query.all()
    orders_list = [o.to_dict() for o in orders]
    return render_template('dashboard/orders.html', orders=orders_list, module_name='Order Management', module_icon='fa-shopping-cart')

@admin_bp.route('/orders/add', methods=['POST'])
@login_required
def add_order():
    try:
        data = request.form
        
        # Check if customer exists
        customer = Customer.query.get(int(data.get('customer_id')))
        if not customer:
            return jsonify({'success': False, 'message': 'Customer not found'}), 400
        
        # Generate order number
        order_count = Order.query.count() + 1
        order_number = f'ORD-{datetime.now().strftime("%Y%m%d")}-{order_count:04d}'

        # Optional coupon / discount information (coming from front website or admin UI)
        discount_id = data.get('discount_id')
        coupon_code = data.get('coupon_code')
        discount_amount = data.get('discount_amount', 0)

        if discount_id:
            try:
                discount_id = int(discount_id)
            except ValueError:
                discount_id = None

        if discount_id is None and coupon_code:
            # Try to resolve discount by code if id not provided
            discount = Discount.query.filter_by(code=coupon_code.upper()).first()
            discount_id = discount.id if discount else None

        try:
            discount_amount = float(discount_amount)
        except (TypeError, ValueError):
            discount_amount = 0

        new_order = Order(
            order_number=order_number,
            customer_id=int(data.get('customer_id')),
            total_amount=float(data.get('total_amount', 0)),
            status=data.get('status', 'pending'),
            discount_id=discount_id,
            coupon_code=coupon_code,
            discount_amount=discount_amount,
            shipping_address=data.get('shipping_address'),
            notes=data.get('notes')
        )

        db.session.add(new_order)

        # If order is immediately completed and has a discount, bump global usage
        increment_global_usage_if_completed(
            discount_id=new_order.discount_id,
            previous_status='pending',
            new_status=new_order.status,
        )

        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Order created successfully', 'data': new_order.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@admin_bp.route('/orders/<int:order_id>/edit', methods=['POST'])
@login_required
def edit_order(order_id):
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'message': 'Order not found'}), 404
        
        data = request.form

        # Track previous status to know when an order transitions to completed
        previous_status = order.status

        order.total_amount = float(data.get('total_amount', order.total_amount))
        order.status = data.get('status', order.status)
        order.shipping_address = data.get('shipping_address', order.shipping_address)
        order.notes = data.get('notes', order.notes)

        # Optional updates for coupon / discount fields
        if 'discount_id' in data or 'coupon_code' in data or 'discount_amount' in data:
            discount_id = data.get('discount_id', order.discount_id)
            coupon_code = data.get('coupon_code', order.coupon_code)
            discount_amount = data.get('discount_amount', order.discount_amount)

            if discount_id:
                try:
                    discount_id = int(discount_id)
                except ValueError:
                    discount_id = order.discount_id

            try:
                discount_amount = float(discount_amount)
            except (TypeError, ValueError):
                discount_amount = order.discount_amount

            order.discount_id = discount_id
            order.coupon_code = coupon_code
            order.discount_amount = discount_amount

        # If order just moved to completed and has a discount, increment global usage
        increment_global_usage_if_completed(
            discount_id=order.discount_id,
            previous_status=previous_status,
            new_status=order.status,
        )

        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Order updated successfully', 'data': order.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@admin_bp.route('/orders/<int:order_id>/delete', methods=['POST', 'DELETE'])
@login_required
def delete_order(order_id):
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'message': 'Order not found'}), 404
        
        db.session.delete(order)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Order deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@admin_bp.route('/api/order-items')
@login_required
def get_all_order_items():
    """Get all order items grouped by order"""
    try:
        order_items = OrderItem.query.all()
        
        # Group items by order_id
        items_by_order = {}
        for item in order_items:
            order_id = item.order_id
            if order_id not in items_by_order:
                items_by_order[order_id] = []
            
            items_by_order[order_id].append({
                'id': item.id,
                'product_name': item.product.name if item.product else 'Unknown',
                'quantity': item.quantity,
                'unit_price': float(item.unit_price)
            })
        
        return jsonify({'success': True, 'items': items_by_order})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400