from flask import Blueprint, render_template, session, redirect, url_for, flash, jsonify
from model.order import Order
from core.database import db
from core.auth_helper import get_customer_session_id, is_customer_logged_in

orders_bp = Blueprint('orders', __name__)


@orders_bp.route('/my-orders')
def my_orders():
    """View customer's orders"""
    if not is_customer_logged_in():
        flash('Please login to view your orders.', 'warning')
        return redirect(url_for('customer_auth.login', next=url_for('orders.my_orders')))
    
    try:
        orders = Order.query.filter_by(customer_id=get_customer_session_id()).order_by(Order.created_at.desc()).all()
        return render_template('frontside/auth/orders.html', title='My Orders - Green Bean', orders=orders)
    except Exception as e:
        flash(f'Error loading orders: {str(e)}', 'danger')
        return redirect(url_for('home.home'))


@orders_bp.route('/order/<int:order_id>')
def order_detail(order_id):
    """View order details"""
    if not is_customer_logged_in():
        flash('Please login to view order details.', 'warning')
        return redirect(url_for('customer_auth.login', next=url_for('orders.order_detail', order_id=order_id)))
    
    try:
        order = Order.query.filter_by(id=order_id, customer_id=get_customer_session_id()).first()
        
        if not order:
            flash('Order not found.', 'danger')
            return redirect(url_for('orders.my_orders'))
        
        return render_template('frontside/auth/order_detail.html', title='Order Details - Green Bean', order=order)
    except Exception as e:
        flash(f'Error loading order details: {str(e)}', 'danger')
        return redirect(url_for('orders.my_orders'))


@orders_bp.route('/order/<int:order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    """Cancel an order"""
    if not is_customer_logged_in():
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    try:
        order = Order.query.filter_by(id=order_id, customer_id=get_customer_session_id()).first()
        
        if not order:
            return jsonify({'success': False, 'message': 'Order not found'}), 404
        
        if order.status not in ['pending', 'processing']:
            return jsonify({'success': False, 'message': 'Order cannot be cancelled in current status'}), 400
        
        order.status = 'cancelled'
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Order cancelled successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
