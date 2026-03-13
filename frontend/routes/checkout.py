from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from datetime import datetime
import json
import os

import stripe
from services.coupons import validate_and_calculate_coupon, CouponError

checkout_bp = Blueprint('checkout', __name__)

# Configure Stripe with secret key from environment
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', '')

TAX_RATE = 0.08
FREE_SHIPPING_THRESHOLD = 50.0


def calculate_order(cart_items, coupon_code=None, customer_id=None, now=None):
    """
    Calculate order summary.

    If both coupon_code and customer_id are provided, validate the coupon
    against the database using services.coupons and apply the discount.
    """
    subtotal = sum(item.get('price', 0) * item.get('quantity', 1) for item in cart_items)

    # Base shipping (before any coupon logic)
    shipping_cost = 0 if subtotal >= FREE_SHIPPING_THRESHOLD else 9.99

    discount = 0.0
    applied_coupon = None
    coupon_error = None

    # Only attempt DB-backed coupon validation if we have both pieces of info
    if coupon_code and customer_id is not None:
        try:
            coupon_result = validate_and_calculate_coupon(
                customer_id=customer_id,
                code=coupon_code,
                subtotal=subtotal,
                now=now,
            )
            discount = float(coupon_result.discount_amount)
            applied_coupon = coupon_result.discount  # Discount model instance
            # Use the service's computed subtotal after coupon
            subtotal_after_coupon = float(coupon_result.new_total)
        except CouponError as e:
            coupon_error = str(e)
            subtotal_after_coupon = subtotal
        except Exception:
            # Any unexpected error: fail safe by ignoring the coupon
            subtotal_after_coupon = subtotal
    else:
        subtotal_after_coupon = subtotal

    # Tax and total based on discounted subtotal
    tax_amount = subtotal_after_coupon * TAX_RATE
    total = subtotal_after_coupon + shipping_cost + tax_amount

    return {
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'tax_amount': tax_amount,
        'discount': discount,
        'total': total,
        'items_count': sum(item.get('quantity', 1) for item in cart_items),
        'applied_coupon': applied_coupon,
        'coupon_error': coupon_error,
    }

@checkout_bp.route('/checkout')
def checkout():
    # Require user to be logged in for checkout
    if 'user_id' not in session:
        flash('Please login to proceed with checkout.', 'warning')
        return redirect(url_for('auth.login', next=url_for('checkout.checkout')))
    
    # Get cart items from session (in a real app you'd get from database based on user)
    cart_items = session.get('cart', [])
    
    # If session cart is empty, redirect back to cart with message
    if not cart_items:
        flash('Your cart is empty. Please add some items before checkout.', 'warning')
        return redirect(url_for('cart.cart'))

    coupon_code = session.get('coupon_code')
    customer_id = session.get('customer_id')  # Assumes you store logged-in customer id in session
    order_summary = calculate_order(cart_items, coupon_code, customer_id)

    stripe_pk = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')

    return render_template(
        'checkout/checkout.html',
        title="Checkout - Green Bean",
        cart_items=cart_items,
        order_summary=order_summary,
        applied_coupon=order_summary.get('applied_coupon'),
        stripe_pk=stripe_pk,
    )

@checkout_bp.route('/checkout/process', methods=['POST'])
def process_checkout():
    # Require user to be logged in for checkout
    if 'user_id' not in session:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Please login to continue'}), 401
        flash('Please login to proceed with checkout.', 'warning')
        return redirect(url_for('auth.login', next=url_for('checkout.checkout')))
    
    try:
        # Get form data
        form_data = request.get_json() if request.is_json else request.form
        
        customer_info = {
            'first_name': form_data.get('first_name'),
            'last_name': form_data.get('last_name'),
            'email': form_data.get('email'),
            'phone': form_data.get('phone'),
            'shipping_address': {
                'street': form_data.get('street_address'),
                'city': form_data.get('city'),
                'state': form_data.get('state'),
                'zip_code': form_data.get('zip_code'),
                'country': form_data.get('country', 'United States')
            },
            'billing_same_as_shipping': form_data.get('billing_same_as_shipping', 'on') == 'on'
        }
        
        # Get cart items
        cart_items = session.get('cart', [])
        
        if not cart_items:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Cart is empty'})
            flash('Cart is empty', 'error')
            return redirect(url_for('cart.cart'))
        
        coupon_code = session.get('coupon_code')
        customer_id = session.get('customer_id')
        order_summary = calculate_order(cart_items, coupon_code, customer_id)
        
        # Generate order ID
        order_id = f"GB{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create order record
        applied_coupon = order_summary.get('applied_coupon')

        order_data = {
            'order_id': order_id,
            'customer_info': customer_info,
            'items': cart_items,
            'order_summary': {
                'subtotal': order_summary['subtotal'],
                'shipping_cost': order_summary['shipping_cost'],
                'tax_amount': order_summary['tax_amount'],
                'discount': order_summary['discount'],
                'total': order_summary['total'],
            },
            'order_date': datetime.now().isoformat(),
            'status': 'confirmed',
            'payment_method': form_data.get('payment_method', 'manual'),
            'applied_coupon': applied_coupon,
            # DB-backed coupon tracking fields
            'discount_id': applied_coupon.id if applied_coupon else None,
            'coupon_code': applied_coupon.code if applied_coupon else None,
            'discount_amount': order_summary['discount'],
        }
        
        # Store order in session (in production, save to database)
        if 'orders' not in session:
            session['orders'] = []
        session['orders'].append(order_data)
        session.modified = True
        
        # Clear cart
        session['cart'] = []
        session.pop('coupon_code', None)
        session.modified = True
        
        if request.is_json:
            return jsonify({
                'success': True, 
                'message': 'Order placed successfully!',
                'order_id': order_id,
                'redirect_url': url_for('checkout.order_confirmation', order_id=order_id)
            })
        else:
            flash('Order placed successfully!', 'success')
            return redirect(url_for('checkout.order_confirmation', order_id=order_id))
            
    except Exception as e:
        if request.is_json:
            return jsonify({'success': False, 'message': f'Error processing order: {str(e)}'})
        flash(f'Error processing order: {str(e)}', 'error')
        return redirect(url_for('checkout.checkout'))


@checkout_bp.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    """Create a Stripe Checkout Session based on the current cart and coupon."""
    if not stripe.api_key:
        return jsonify({'error': 'Stripe is not configured on the server.'}), 500

    cart_items = session.get('cart', [])
    if not cart_items:
        return jsonify({'error': 'Your cart is empty.'}), 400

    coupon_code = session.get('coupon_code')
    customer_id = session.get('customer_id')
    order_summary = calculate_order(cart_items, coupon_code, customer_id)

    try:
        # Build line items for Stripe (prices in cents)
        line_items = []
        for item in cart_items:
            quantity = int(item.get('quantity', 1))
            price = float(item.get('price', 0.0))
            if quantity <= 0 or price <= 0:
                continue
            unit_amount = int(round(price * 100))
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': item.get('name', 'Plant')},
                    'unit_amount': unit_amount,
                },
                'quantity': quantity,
            })

        # Apply discount by reducing line item prices proportionally (simple demo approach)
        discount = order_summary['discount']
        if discount > 0 and order_summary['subtotal'] > 0 and line_items:
            discount_factor = max(
                0.0,
                (order_summary['subtotal'] - discount) / order_summary['subtotal'],
            )
            for li in line_items:
                base_amount = li['price_data']['unit_amount']
                li['price_data']['unit_amount'] = max(
                    1, int(round(base_amount * discount_factor))
                )

        # Add shipping as a separate line item if needed
        if order_summary['shipping_cost'] > 0:
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': 'Shipping'},
                    'unit_amount': int(round(order_summary['shipping_cost'] * 100)),
                },
                'quantity': 1,
            })

        # Add tax as a separate line item (demo only – in production use Stripe tax features)
        if order_summary['tax_amount'] > 0:
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': 'Tax'},
                    'unit_amount': int(round(order_summary['tax_amount'] * 100)),
                },
                'quantity': 1,
            })

        # Basic customer info (email is helpful for Stripe receipts)
        data = request.get_json(silent=True) or {}
        customer_email = data.get('email')

        checkout_session = stripe.checkout.Session.create(
            mode='payment',
            payment_method_types=['card'],
            line_items=line_items,
            success_url=url_for('checkout.checkout_success', _external=True)
            + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('checkout.checkout', _external=True),
            customer_email=customer_email or None,
        )

        return jsonify({'id': checkout_session.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@checkout_bp.route('/checkout/success')
def checkout_success():
    """Handle return from Stripe Checkout and record a simple order."""
    session_id = request.args.get('session_id')
    if not session_id or not stripe.api_key:
        flash('Payment verification failed.', 'error')
        return redirect(url_for('checkout.checkout'))

    try:
        stripe_session = stripe.checkout.Session.retrieve(session_id)
        if stripe_session.payment_status != 'paid':
            flash('Payment not completed.', 'error')
            return redirect(url_for('checkout.checkout'))
    except Exception as e:
        flash(f'Error verifying payment: {str(e)}', 'error')
        return redirect(url_for('checkout.checkout'))

    cart_items = session.get('cart', [])
    if not cart_items:
        # Cart might already be cleared; just show generic success
        flash('Payment completed successfully.', 'success')
        return redirect(url_for('shop.shop'))

    coupon_code = session.get('coupon_code')
    customer_id = session.get('customer_id')
    order_summary = calculate_order(cart_items, coupon_code, customer_id)

    order_id = f"GB{datetime.now().strftime('%Y%m%d%H%M%S')}"

    order_data = {
        'order_id': order_id,
        'customer_info': {
            'first_name': '',
            'last_name': '',
            'email': stripe_session.get('customer_details', {}).get('email'),
            'phone': '',
            'shipping_address': {},
            'billing_same_as_shipping': True,
        },
        'items': cart_items,
        'order_summary': {
            'subtotal': order_summary['subtotal'],
            'shipping_cost': order_summary['shipping_cost'],
            'tax_amount': order_summary['tax_amount'],
            'discount': order_summary['discount'],
            'total': order_summary['total'],
        },
        'order_date': datetime.now().isoformat(),
        'status': 'paid',
        'payment_method': 'stripe_checkout',
        'applied_coupon': order_summary.get('applied_coupon'),
    }

    if 'orders' not in session:
        session['orders'] = []
    session['orders'].append(order_data)

    # Clear cart and coupon
    session['cart'] = []
    session.pop('coupon_code', None)
    session.modified = True

    flash('Payment completed and order confirmed!', 'success')
    return redirect(url_for('checkout.order_confirmation', order_id=order_id))

@checkout_bp.route('/order-confirmation/<order_id>')
def order_confirmation(order_id):
    # Find order in session
    orders = session.get('orders', [])
    order = next((o for o in orders if o['order_id'] == order_id), None)
    
    if not order:
        flash('Order not found', 'error')
        return redirect(url_for('shop.shop'))
    
    return render_template('checkout/order_confirmation.html', 
                         title=f"Order Confirmation - {order_id}", 
                         order=order)

@checkout_bp.route('/my-orders')
def my_orders():
    # Get all orders for the user
    orders = session.get('orders', [])
    return render_template('checkout/my_orders.html', 
                         title="My Orders - Green Bean", 
                         orders=orders)