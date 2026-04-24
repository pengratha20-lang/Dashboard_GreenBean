from flask import render_template, request, jsonify, Blueprint, make_response
from core.database import db
from core.auth_helper import login_required
from model.order import Order, OrderItem
from model.order_status_history import OrderStatusHistory
from model.customer import Customer
from model.discount import Discount
from datetime import datetime
from services.main.dashboard.coupons import increment_global_usage_if_completed
from core.helpers import DataExporter, FormErrorHandler

# Create Blueprint
order_bp = Blueprint('order_module', __name__, url_prefix='')

@order_bp.route('/orders')
@login_required
def orders_route():
    orders = Order.query.order_by(Order.created_at.desc(), Order.id.desc()).all()
    orders_list = [o.to_dict() for o in orders]
    customers = Customer.query.order_by(Customer.name.asc()).all()
    customer_options = [{'id': customer.id, 'name': customer.name, 'email': customer.email} for customer in customers]
    return render_template(
        'dashboard/orders.html',
        orders=orders_list,
        customers=customer_options,
        module_name='Order Management',
        module_icon='fa-shopping-cart'
    )

@order_bp.route('/orders/add', methods=['POST'])
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

        # Optional coupon / discount information
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
            currency=(data.get('currency') or 'USD').upper(),
            payment_method=(data.get('payment_method') or 'credit_card').lower(),
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

@order_bp.route('/orders/<int:order_id>/edit', methods=['POST'])
@login_required
def edit_order(order_id):
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'message': 'Order not found'}), 404
        
        data = request.form

        # Track previous status to know when an order transitions to completed
        previous_status = order.status
        new_status = data.get('status', order.status)

        order.total_amount = float(data.get('total_amount', order.total_amount))
        order.currency = (data.get('currency', order.currency) or order.currency or 'USD').upper()
        order.payment_method = (data.get('payment_method', order.payment_method) or order.payment_method or 'credit_card').lower()
        order.status = new_status
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

        # Record status change in history
        if previous_status != new_status:
            OrderStatusHistory.create_entry(
                order_id=order_id,
                old_status=previous_status,
                new_status=new_status,
                changed_by='admin',
                notes=data.get('status_notes', '')
            )

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
        error_info = FormErrorHandler.get_user_friendly_error(str(e))
        return jsonify({'success': False, 'message': error_info.get('message', str(e))}), 400

@order_bp.route('/orders/<int:order_id>/delete', methods=['POST', 'DELETE'])
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

@order_bp.route('/api/order-items')
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
                'product_name': item.product.product_name if item.product else 'Unknown',
                'quantity': item.quantity,
                'unit_price': float(item.unit_price)
            })
        
        return jsonify({'success': True, 'items': items_by_order})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@order_bp.route('/api/notifications')
@login_required
def get_notifications():
    """Real time Vue polling endpoint for pending orders"""
    try:
        pending_count = Order.query.filter_by(status='pending').count()
        return jsonify({'success': True, 'pending_orders_count': pending_count})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


# ============ NEW FEATURES ============

@order_bp.route('/orders/<int:order_id>/timeline')
@login_required
def get_order_timeline(order_id):
    """Get order status history/timeline"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'message': 'Order not found'}), 404
        
        # Get status history
        history = OrderStatusHistory.query.filter_by(order_id=order_id).order_by(
            OrderStatusHistory.created_at.asc()
        ).all()
        
        timeline = []
        
        # Add creation event
        if order.created_at:
            timeline.append({
                'status': 'created',
                'old_status': None,
                'new_status': 'pending',
                'timestamp': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'changed_by': 'system',
                'notes': 'Order created'
            })
        
        # Add status changes
        for entry in history:
            timeline.append({
                'status': entry.new_status,
                'old_status': entry.old_status,
                'new_status': entry.new_status,
                'timestamp': entry.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'changed_by': entry.changed_by,
                'notes': entry.notes or 'Status updated'
            })
        
        return jsonify({'success': True, 'timeline': timeline, 'current_status': order.status})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@order_bp.route('/orders/export', methods=['POST'])
@login_required
def export_orders():
    """Export orders to CSV"""
    try:
        # Get filter parameters
        status_filter = request.form.get('status', '')
        date_from = request.form.get('date_from', '')
        date_to = request.form.get('date_to', '')
        
        # Build query
        query = Order.query
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        if date_from:
            try:
                from_date = datetime.fromisoformat(date_from)
                query = query.filter(Order.created_at >= from_date)
            except:
                pass
        
        if date_to:
            try:
                to_date = datetime.fromisoformat(date_to)
                query = query.filter(Order.created_at <= to_date)
            except:
                pass
        
        orders = query.all()
        export_data = DataExporter.prepare_order_export(orders)
        columns = ['Order #', 'Customer', 'Email', 'Total', 'Status', 'Date', 'Items']
        
        csv_content = DataExporter.export_to_csv(export_data, columns)
        
        response = make_response(csv_content)
        response.headers['Content-Disposition'] = 'attachment; filename=orders.csv'
        response.headers['Content-Type'] = 'text/csv'
        
        return response
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@order_bp.route('/api/orders/search', methods=['POST'])
@login_required
def search_orders():
    """Search orders by various criteria"""
    try:
        search_term = request.json.get('q', '').strip().lower()
        search_type = request.json.get('type', 'all')  # all, order_number, customer, email
        limit = request.json.get('limit', 20)
        
        query = Order.query
        
        if search_term:
            if search_type in ['all', 'order_number']:
                query = query.filter(Order.order_number.ilike(f'%{search_term}%'))
            elif search_type in ['all', 'customer']:
                # Search by customer name
                customer_query = Customer.query.filter(
                    Customer.name.ilike(f'%{search_term}%')
                ).all()
                customer_ids = [c.id for c in customer_query]
                query = query.filter(Order.customer_id.in_(customer_ids) if customer_ids else False)
            elif search_type in ['all', 'email']:
                # Search by customer email
                customer_query = Customer.query.filter(
                    Customer.email.ilike(f'%{search_term}%')
                ).all()
                customer_ids = [c.id for c in customer_query]
                query = query.filter(Order.customer_id.in_(customer_ids) if customer_ids else False)
        
        results = query.limit(limit).all()
        
        return jsonify({
            'success': True,
            'results': [o.to_dict() for o in results],
            'count': len(results)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400
