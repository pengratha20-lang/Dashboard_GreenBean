from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
import base64
from datetime import datetime
import inspect
from io import BytesIO
import json
import os
from decimal import Decimal, InvalidOperation
from types import SimpleNamespace
from core.database import db
from model.order import Order, OrderItem
from services.main.frontside.coupons import validate_and_calculate_coupon, CouponError
from functools import wraps
import logging
import qrcode
from bakong_khqr import KHQR
from core.auth_helper import get_customer_session_id, is_customer_logged_in
from core.validators import (
    validate_payment_method,
    validate_currency,
    validate_amount,
    validate_email,
    validate_phone,
)
from core.exceptions import (
    InvalidPaymentMethod, InvalidCurrency, InvalidAmount, KHQRError, InvalidKHQRConfig
)
from config.constants import PAYMENT_CONFIG, KHQR_CONFIG
from core.security import security_logger, app_logger

checkout_bp = Blueprint('checkout', __name__)

# Use constants instead of hardcoded values
TAX_RATE = PAYMENT_CONFIG['TAX_RATE']
FREE_SHIPPING_THRESHOLD = PAYMENT_CONFIG['FREE_SHIPPING_THRESHOLD']
ALLOWED_PAYMENT_METHODS = PAYMENT_CONFIG['ALLOWED_METHODS']
ALLOWED_CURRENCIES = PAYMENT_CONFIG['ALLOWED_CURRENCIES']

KHQR_DEFAULT_CITY = KHQR_CONFIG['DEFAULT_CITY']
KHQR_DEFAULT_MCC = KHQR_CONFIG['DEFAULT_MCC']
KHQR_COUNTRY_CODE = KHQR_CONFIG['COUNTRY_CODE']
KHQR_CURRENCY_MAP = KHQR_CONFIG['CURRENCY_MAP']

# Initialize KHQR with bakong-khqr library
BAKONG_API_KEY = os.getenv('BAKONG_API_KEY', '')
_khqr_instance = None
_create_qr_signature = None

def _get_khqr():
    """Get or create KHQR instance"""
    global _khqr_instance
    if _khqr_instance is None:
        if not BAKONG_API_KEY:
            raise KHQRError("BAKONG_API_KEY not configured")
        _khqr_instance = KHQR(BAKONG_API_KEY)
    return _khqr_instance


def _get_create_qr_signature():
    """Cache the KHQR.create_qr signature so we can support multiple library versions."""
    global _create_qr_signature
    if _create_qr_signature is None:
        _create_qr_signature = inspect.signature(KHQR.create_qr)
    return _create_qr_signature


def _normalize_bakong_account_id(account_id):
    """
    Keep the teacher sample's permissive account handling.
    Some merchants use `username@bkrt`, while others may use phone or plain IDs.
    """
    normalized_account = (account_id or '').strip()
    if not normalized_account:
        security_logger.log_suspicious_activity(
            'invalid_khqr_config',
            details='Missing BAKONG_ACCOUNT_ID'
        )
        raise InvalidKHQRConfig()
    return normalized_account


def _build_create_qr_kwargs(order, amount, mode):
    """Build KHQR arguments in a way that works with both old and new bakong-khqr versions."""
    create_qr_signature = _get_create_qr_signature()
    supports_expiration = 'expiration' in create_qr_signature.parameters

    bakong_account_id = _normalize_bakong_account_id(os.getenv('BAKONG_ACCOUNT_ID', ''))
    merchant_name = os.getenv('BAKONG_MERCHANT_NAME', 'Green Bean').strip()[:25]
    merchant_city = os.getenv('BAKONG_MERCHANT_CITY', KHQR_DEFAULT_CITY).strip()[:15] or KHQR_DEFAULT_CITY
    store_label = os.getenv('BAKONG_STORE_LABEL', 'Green Bean').strip()[:25]
    phone_number = os.getenv('BAKONG_MOBILE_NUMBER', '').strip()[:25]
    terminal_label = os.getenv('BAKONG_TERMINAL_LABEL', 'POS-01').strip()[:25] or 'POS-01'

    qr_kwargs = {
        'bank_account': bakong_account_id,
        'merchant_name': merchant_name,
        'merchant_city': merchant_city,
        'amount': float(amount),
        'currency': (order.currency or 'KHR').upper(),
        'store_label': store_label,
        'phone_number': phone_number,
        'bill_number': order.order_number[:25] if order.order_number else ('STATIC' if mode == 'static' else 'DYNAMIC'),
        'terminal_label': terminal_label,
        # Make the QR type explicit instead of relying on library defaults.
        'static': mode == 'static',
    }

    if supports_expiration and mode != 'static':
        try:
            qr_kwargs['expiration'] = max(1, int(os.getenv('BAKONG_QR_EXPIRATION_DAYS', '2')))
        except (TypeError, ValueError):
            qr_kwargs['expiration'] = 2

    return qr_kwargs


def _generate_qr_code_data_url(qr_payload):
    """
    Generate the QR image with the plain `qrcode` library first to mirror the teacher sample.
    Fall back to bakong-khqr image generation if Pillow/qrcode processing fails.
    """
    try:
        qr_image = qrcode.make(qr_payload)
        buffer = BytesIO()
        qr_image.save(buffer, format='PNG')
        encoded_image = base64.b64encode(buffer.getvalue()).decode('ascii')
        return f'data:image/png;base64,{encoded_image}'
    except Exception:
        khqr_instance = _get_khqr()
        return khqr_instance.qr_image(qr_payload, format='base64_uri')


def generate_khqr_payload(order, amount, mode='dynamic'):
    """
    Generate a KHQR-compliant payload using bakong-khqr library.
    Works with all KHQR-compliant banks: ABA, Bakong, Canadia, Wing, etc.
    
    Returns: qr_payload (MD5 is generated separately)
    """
    try:
        # Validate inputs
        currency = validate_currency((order.currency or 'USD').upper(), ALLOWED_CURRENCIES)
        mode = str(mode).lower() if mode else 'dynamic'
        
        if mode not in ['static', 'dynamic']:
            raise KHQRError(f"Invalid QR mode: {mode}")
        
        # For static QR, amount should be 0; for dynamic QR, validate normally
        if mode == 'static':
            if amount != 0:
                raise KHQRError("Static QR must have amount=0")
            validated_amount = Decimal('0')
        else:
            validated_amount = validate_amount(amount)

        # Get KHQR instance and generate payload
        khqr_instance = _get_khqr()

        qr_kwargs = _build_create_qr_kwargs(order, validated_amount, mode)
        qr_kwargs['currency'] = currency
        qr_payload = khqr_instance.create_qr(**qr_kwargs)
        
        print(f'📋 Generated KHQR Payload: {len(qr_payload)} chars')
        
        return qr_payload
    
    except (InvalidCurrency, InvalidAmount) as e:
        raise KHQRError(str(e))
    except Exception as e:
        app_logger.log_error('KHQRPayloadGenerationError', str(e))
        raise KHQRError(f"Failed to generate KHQR payload: {str(e)}")


def calculate_order(cart_items, coupon_code=None, customer_id=None, now=None, shipping_method=None):
    """
    Calculate order summary.
    Supports optional shipping_method parameter to use specific shipping cost.
    Shipping methods and costs:
    - 'vireakbunthan-pp': $2.50
    - 'vireakbunthan-prov': $5.00
    - 'jnt-pp': $3.00
    - 'jnt-prov': $6.00
    - 'test': $0.00 (free for testing)
    """
    subtotal = sum(item.get('price', 0) * item.get('quantity', 1) for item in cart_items)

    # Shipping costs mapping
    SHIPPING_COSTS = {
        'vireakbunthan-pp': 2.50,
        'vireakbunthan-prov': 5.00,
        'jnt-pp': 3.00,
        'jnt-prov': 6.00,
        'test': 0.00
    }
    
    # Get shipping cost from mapping, or default to $0 if subtotal >= threshold
    if shipping_method and shipping_method in SHIPPING_COSTS:
        shipping_cost = SHIPPING_COSTS[shipping_method]
    else:
        # Default: free shipping if subtotal >= threshold
        shipping_cost = 0 if subtotal >= FREE_SHIPPING_THRESHOLD else 2.50  # Default to cheapest option

    discount = 0.0
    applied_coupon = None
    coupon_error = None

    if coupon_code and customer_id is not None:
        try:
            coupon_result = validate_and_calculate_coupon(
                customer_id=customer_id,
                code=coupon_code,
                subtotal=subtotal,
                now=now,
            )
            discount = float(coupon_result.discount_amount)
            applied_coupon = coupon_result.discount
        except CouponError as e:
            coupon_error = str(e)
        except Exception:
            pass

    # No tax - removed from order total
    tax_amount = 0
    total = (subtotal - discount) + shipping_cost

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


def build_order_summary(cart_items, coupon_code=None, customer_id=None, now=None, include_shipping=True, shipping_method=None):
    """
    Wrap order calculation so test utilities can opt out of shipping without changing
    the real checkout behavior.
    Supports optional shipping_method parameter to override default shipping calculation.
    """
    summary = calculate_order(cart_items, coupon_code, customer_id, now=now, shipping_method=shipping_method)
    if include_shipping:
        return summary

    adjusted_summary = dict(summary)
    adjusted_summary['shipping_cost'] = 0.0
    adjusted_summary['total'] = max(0.0, float(summary['subtotal']) - float(summary['discount']))
    return adjusted_summary


def _safe_api_error(public_message, status_code=400, internal_error=None, log_prefix='ApiError'):
    """Return a standardized API error payload and keep internal details in logs."""
    if internal_error is not None:
        app_logger.log_error(log_prefix, str(internal_error))
    return jsonify({'success': False, 'message': public_message}), status_code


def _validate_checkout_customer_info(name, email, phone, address, city, country):
    """Validate and sanitize checkout customer input."""
    cleaned = {
        'name': (name or '').strip()[:100],
        'email': (email or '').strip()[:120],
        'phone': (phone or '').strip()[:20],
        'address': (address or '').strip()[:255],
        'city': (city or '').strip()[:100],
        'country': (country or '').strip()[:100],
    }

    required_fields = [key for key, value in cleaned.items() if not value]
    if required_fields:
        raise ValueError(f'Missing required fields: {", ".join(required_fields)}')

    if len(cleaned['name']) < 2:
        raise ValueError('Name must be at least 2 characters')
    if len(cleaned['address']) < 5:
        raise ValueError('Address must be at least 5 characters')
    if len(cleaned['city']) < 2:
        raise ValueError('City must be at least 2 characters')
    if len(cleaned['country']) < 2:
        raise ValueError('Country must be at least 2 characters')

    try:
        cleaned['email'] = validate_email(cleaned['email'])
    except Exception:
        raise ValueError('Invalid email format')

    try:
        cleaned['phone'] = validate_phone(cleaned['phone'])
    except Exception:
        raise ValueError('Invalid phone format')

    return cleaned


def _validate_cart_inventory(cart_items):
    """Validate cart item payload and ensure stock is still available."""
    from model.product import Product

    validated_items = []
    for raw_item in cart_items:
        try:
            product_id = int(raw_item.get('id'))
            quantity = int(raw_item.get('quantity', 1))
        except (TypeError, ValueError):
            raise ValueError('Invalid cart item data')

        if quantity < 1:
            raise ValueError('Invalid product quantity in cart')

        product = Product.query.get(product_id)
        if not product:
            raise ValueError(f'Product with ID {product_id} is no longer available')

        if product.stock < quantity:
            raise ValueError(
                f'Not enough stock for {product.product_name}. Available: {product.stock}'
            )

        validated_items.append({
            'product': product,
            'product_id': product_id,
            'quantity': quantity,
            # Always trust database price, never client/session price.
            'unit_price': float(product.price or 0),
        })

    return validated_items


def _create_order_with_invoice(
    *,
    cart_items,
    customer_id,
    currency,
    payment_method,
    coupon_code,
    order_summary,
    name,
    email,
    phone,
    address,
    city,
    country,
    reserve_stock=False,
    validated_items=None,
):
    """Create order + order items + invoice in one DB transaction."""
    from model.invoice import Invoice

    if validated_items is None:
        validated_items = _validate_cart_inventory(cart_items)
    order_number = f"GB-{datetime.now().strftime('%Y%m%d')}-{os.urandom(4).hex().upper()}"

    new_order = Order(
        order_number=order_number,
        customer_id=customer_id,
        customer_name=name,  # ✅ Store customer name for guest orders and Telegram notifications
        total_amount=float(order_summary['total']),
        currency=currency,
        payment_method=payment_method,
        status='pending',
        coupon_code=coupon_code if coupon_code else None,
        discount_amount=float(order_summary['discount']),
        shipping_address=f"{address}, {city}, {country}",
    )
    db.session.add(new_order)
    db.session.flush()

    for item in validated_items:
        db.session.add(OrderItem(
            order_id=new_order.id,
            product_id=item['product_id'],
            quantity=item['quantity'],
            unit_price=item['unit_price'],
        ))

        if reserve_stock:
            # Use row-level lock to prevent concurrent stock deductions (race condition fix)
            from sqlalchemy import text
            db.session.execute(
                text('SELECT * FROM product WHERE id = :id FOR UPDATE'),
                {'id': item['product_id']}
            )
            
            # Re-fetch product with lock and check stock again
            product_obj = item['product']
            db.session.refresh(product_obj)
            
            # Re-check after lock acquisition to prevent overselling
            if product_obj.stock < item['quantity']:
                raise ValueError(
                    f'Not enough stock for {product_obj.product_name}. Available: {product_obj.stock}'
                )
            product_obj.stock -= item['quantity']

    invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{new_order.id}"
    invoice = Invoice(
        order_id=new_order.id,
        invoice_number=invoice_number,
        customer_name=name,
        customer_email=email,
        customer_phone=phone,
        shipping_address=f"{address}, {city}, {country}",
        subtotal=float(order_summary['subtotal']),
        shipping_cost=float(order_summary['shipping_cost']),
        discount_amount=float(order_summary['discount']),
        total_amount=float(order_summary['total']),
        payment_method=payment_method,
        status='issued',
    )
    db.session.add(invoice)
    db.session.commit()

    return new_order, invoice


def _build_checkout_display_cart(cart_items):
    """Build a display-safe cart payload from verified DB products."""
    verified_items = _validate_cart_inventory(cart_items)
    display_items = []
    summary_items = []

    for item in verified_items:
        product = item['product']
        quantity = item['quantity']
        unit_price = float(item['unit_price'])

        display_items.append({
            'id': item['product_id'],
            'name': product.product_name,
            'price': unit_price,
            'quantity': quantity,
            'image': product.get_card_image_url(),
            'description': product.description or '',
            'category': getattr(product.category, 'category_name', '') if getattr(product, 'category', None) else '',
            'inStock': product.stock > 0,
        })
        summary_items.append({
            'id': item['product_id'],
            'price': unit_price,
            'quantity': quantity,
        })

    return display_items, summary_items

@checkout_bp.route('/checkout')
def checkout():
    # Allow both guests and logged-in users
    cart_items = session.get('cart', [])
    if not cart_items:
        flash('Your cart is empty. Please add some items before checkout.', 'warning')
        return redirect(url_for('cart.cart'))

    try:
        display_cart_items, summary_cart_items = _build_checkout_display_cart(cart_items)
    except ValueError as exc:
        flash(str(exc), 'warning')
        session['cart'] = []
        session.modified = True
        return redirect(url_for('cart.cart'))

    # Keep normalized cart shape in session to prevent template/key mismatches.
    session['cart'] = display_cart_items
    session.modified = True

    coupon_code = session.get('coupon_code')
    customer_id = get_customer_session_id()  # Will be None for guests, which is okay
    # Pass default shipping method (vireakbunthan-pp is selected by default in HTML)
    order_summary = calculate_order(summary_cart_items, coupon_code, customer_id, shipping_method='vireakbunthan-pp')

    # Get customer info if logged in
    customer_info = {}
    if customer_id:
        from model.customer import Customer
        customer = Customer.query.get(customer_id)
        if customer:
            customer_info = {
                'name': customer.name or '',
                'email': customer.email or '',
                'phone': customer.phone or '',
                'address': customer.address or '',
                'city': customer.city or '',
                'country': customer.country or ''
            }

    return render_template(
        'frontside/checkout/checkout.html',
        title="Checkout - Green Bean",
        cart_items=display_cart_items,
        order_summary=order_summary,
        applied_coupon=order_summary.get('applied_coupon'),
        is_guest=not is_customer_logged_in(),
        customer_info=customer_info,
        customer_id=customer_id  # ✅ Pass customer_id to frontend for coupon validation
    )

@checkout_bp.route('/test-bakong')
def test_bakong():
    """Simple test page for Bakong payment flow"""
    bakong_reference_deeplink = (
        request.args.get('deeplink', '').strip()
        or os.getenv('BAKONG_TEST_DEEPLINK_URL', '').strip()
    )

    bakong_sample_payload = None
    bakong_sample_error = None

    try:
        sample_order = SimpleNamespace(currency='USD', order_number='TEST-BAKONG')
        bakong_sample_payload = generate_khqr_payload(sample_order, Decimal('0'), mode='static')
    except Exception as exc:
        bakong_sample_error = str(exc)

    return render_template(
        'frontside/checkout/test_bakong.html',
        bakong_account_id=os.getenv('BAKONG_ACCOUNT_ID', '').strip(),
        bakong_merchant_name=os.getenv('BAKONG_MERCHANT_NAME', '').strip(),
        bakong_merchant_city=os.getenv('BAKONG_MERCHANT_CITY', '').strip(),
        bakong_reference_deeplink=bakong_reference_deeplink,
        bakong_sample_payload=bakong_sample_payload,
        bakong_sample_error=bakong_sample_error,
    )

@checkout_bp.route('/simple-qr-test')
def simple_qr_test():
    """Simplified QR test page - easier to verify"""
    return render_template('frontside/checkout/simple_qr_test.html')

@checkout_bp.route('/api/test-product', methods=['GET'])
def get_test_product():
    """Get first valid product from database for test purposes"""
    try:
        from model.product import Product
        from core.database import db
        
        product = db.session.query(Product).filter(Product.stock > 0).first()
        
        if not product:
            return jsonify({'success': False, 'message': 'No products available in database'}), 404
        
        return jsonify({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.product_name,
                'price': float(product.price),
                'stock': product.stock,
                'image': product.image or '/static/images/placeholder.jpg',
                'description': product.description or 'Test Product'
            }
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@checkout_bp.route('/api/test-telegram', methods=['GET'])
def test_telegram_notification():
    """Test if Telegram bot is working"""
    try:
        from routes.integrations.telegram_service import get_telegram_notifier
        notifier = get_telegram_notifier()
        
        if not notifier.enabled:
            return jsonify({
                'success': False,
                'message': 'Telegram notifications not enabled. Check TELEGRAM_BOT_TOKEN and TELEGRAM_ADMIN_USER_ID in .env'
            }), 400
        
        # Send test notification
        result = notifier.send_test_notification()
        
        if result:
            return jsonify({
                'success': True,
                'message': '✅ Test notification sent! Check your Telegram app.'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '❌ Failed to send notification. Check bot token and user ID.'
            }), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@checkout_bp.route('/api/test-create-order-custom', methods=['POST'])
def test_create_order_custom():
    """Create a test order with custom amount (for testing purposes only)"""
    try:
        from model.order import Order
        from core.database import db
        import uuid
        
        data = request.get_json()
        amount = float(data.get('amount', 1.00))
        
        if amount < 0.01:
            return jsonify({'success': False, 'message': 'Minimum amount is $0.01'}), 400
        
        # Create a test order
        test_order = Order(
            order_number=f'TEST-{uuid.uuid4().hex[:8].upper()}',
            customer_id=None,
            name='Test User',
            email='test@example.com',
            phone='012345678',
            address='Test Address',
            city='Test City',
            country='Cambodia',
            currency='USD',
            total_amount=amount,
            subtotal=amount,
            shipping_cost=0,
            tax_amount=0,
            discount_amount=0,
            payment_method='bakong',
            status='pending'
        )
        
        db.session.add(test_order)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'order_id': test_order.id,
            'amount': float(test_order.total_amount),
            'order_number': test_order.order_number
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@checkout_bp.route('/checkout/process', methods=['POST'])
def process_checkout():
    """
    Process checkout with enhanced security:
    - Payment method validation
    - CSRF token checking
    - Input sanitization
    - Error logging and user-friendly messages
    """
    try:
        # Get form data
        if request.is_json:
            form_data = request.get_json()
        else:
            form_data = request.form
        
        # Validate cart
        cart_items = session.get('cart', [])
        if not cart_items:
            app_logger.log_error('CheckoutError', 'Empty cart checkout attempt')
            security_logger.log_suspicious_activity(
                'empty_cart_checkout',
                ip_address=request.remote_addr
            )
            return jsonify({'error': 'Cart is empty'}), 400
        
        # Get payment method and validate it (whitelist validation)
        payment_method = form_data.get('payment_method', 'credit_card').lower()
        try:
            payment_method = validate_payment_method(payment_method, ALLOWED_PAYMENT_METHODS)
        except InvalidPaymentMethod:
            security_logger.log_suspicious_activity(
                'invalid_payment_method',
                details=f'Attempted: {payment_method}'
            )
            return jsonify({'error': 'Invalid payment method'}), 400
        
        # Get currency and validate
        currency = form_data.get('currency', 'USD').upper()
        try:
            currency = validate_currency(currency, ALLOWED_CURRENCIES)
        except InvalidCurrency:
            security_logger.log_suspicious_activity(
                'invalid_currency',
                details=f'Attempted: {currency}'
            )
            currency = 'USD'  # Default to USD for security
        
        validated_items = _validate_cart_inventory(cart_items)

        # Calculate order using verified DB prices.
        coupon_code = session.get('coupon_code')
        customer_id = get_customer_session_id()
        shipping_method = form_data.get('shipping')  # Get selected shipping method
        verified_cart_items = [
            {
                'id': item['product_id'],
                'price': item['unit_price'],
                'quantity': item['quantity'],
            }
            for item in validated_items
        ]
        order_summary = calculate_order(verified_cart_items, coupon_code, customer_id, shipping_method=shipping_method)

        # Validate checkout customer fields with explicit formatting rules.
        customer_data = _validate_checkout_customer_info(
            form_data.get('name'),
            form_data.get('email'),
            form_data.get('phone'),
            form_data.get('address'),
            form_data.get('city'),
            form_data.get('country'),
        )
        
        new_order, invoice = _create_order_with_invoice(
            cart_items=cart_items,
            customer_id=customer_id,
            currency=currency,
            payment_method=payment_method,
            coupon_code=coupon_code,
            order_summary=order_summary,
            name=customer_data['name'],
            email=customer_data['email'],
            phone=customer_data['phone'],
            address=customer_data['address'],
            city=customer_data['city'],
            country=customer_data['country'],
            reserve_stock=True,
            validated_items=validated_items,
        )
        order_number = new_order.order_number
        invoice_number = invoice.invoice_number
        
        # Log the successful order creation
        security_logger.info(f'Order created successfully: {order_number} | Payment Method: {payment_method} | Customer ID: {customer_id} | IP: {request.remote_addr}')
        security_logger.info(f'Invoice generated: {invoice_number} for Order {order_number}')
        
        # Clear session cart
        session['cart'] = []
        session.pop('coupon_code', None)
        session.modified = True
        
        # Store order info for guest checkout
        if customer_id is None:
            session['guest_order_id'] = new_order.id
            session.modified = True
        
        # Return response
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Order placed successfully!',
                'order_id': new_order.id,
                'order_number': order_number,
                'payment_method': payment_method,
                'redirect_url': url_for('checkout.order_confirmation', order_id=new_order.id)
            }), 201
        else:
            flash(f'Order placed successfully! Order #: {order_number}', 'success')
            return redirect(url_for('checkout.order_confirmation', order_id=new_order.id))
            
    except ValueError as ve:
        app_logger.log_error('CheckoutValueError', str(ve))
        db.session.rollback()
        if request.is_json:
            return _safe_api_error(str(ve), 400)
        flash(str(ve), 'error')
        return redirect(url_for('checkout.checkout'))
    
    except (InvalidPaymentMethod, InvalidCurrency, InvalidAmount, KHQRError) as e:
        app_logger.log_error(type(e).__name__, str(e))
        db.session.rollback()
        if request.is_json:
            return _safe_api_error('Invalid checkout request', 400, internal_error=e, log_prefix=type(e).__name__)
        flash(str(e), 'error')
        return redirect(url_for('checkout.checkout'))
        
    except Exception as e:
        app_logger.log_error('UnexpectedCheckoutError', str(e))
        db.session.rollback()
        if request.is_json:
            return _safe_api_error('Error processing order', 500, internal_error=e, log_prefix='UnexpectedCheckoutError')
        flash('An error occurred while processing your order. Please try again.', 'error')
        return redirect(url_for('checkout.checkout'))

@checkout_bp.route('/order-confirmation/<int:order_id>')
def order_confirmation(order_id):
    from model.invoice import Invoice

    order = Order.query.get(order_id)
    
    if not order:
        flash('Order not found', 'error')
        return redirect(url_for('shop.shop'))
    
    # Allow viewing if:
    # 1. User is logged in and owns the order, OR
    # 2. This is a guest order just placed (in session)
    user_id = get_customer_session_id()
    guest_order_id = session.get('guest_order_id')
    
    if order.customer_id and order.customer_id != user_id:
        # Logged in but doesn't own this order
        security_logger.warning(f'Unauthorized order access attempt: Order {order_id} by User {user_id} from IP: {request.remote_addr}')
        flash('You do not have permission to view this order', 'error')
        return redirect(url_for('shop.shop'))
    
    if not order.customer_id and guest_order_id != order_id:
        # Guest order but not the one just placed
        flash('Order not found', 'error')
        return redirect(url_for('shop.shop'))
    
    # Clear guest order from session after viewing
    if guest_order_id == order_id:
        session.pop('guest_order_id', None)

    invoice = Invoice.query.filter_by(order_id=order_id).first()

    # Build template-friendly order view model (legacy template compatibility).
    order_items = []
    for line in order.order_items:
        product = line.product
        order_items.append({
            'name': product.product_name if product else f'Product #{line.product_id}',
            'description': product.description if product and product.description else '',
            'image': product.get_card_image_url() if product else '/static/images/default-product.png',
            'quantity': int(line.quantity or 0),
            'price': float(line.unit_price or 0),
        })

    raw_shipping = (invoice.shipping_address if invoice else order.shipping_address) or ''
    shipping_parts = [part.strip() for part in raw_shipping.split(',') if part.strip()]
    street = shipping_parts[0] if len(shipping_parts) > 0 else raw_shipping
    city = shipping_parts[1] if len(shipping_parts) > 1 else ''
    country = shipping_parts[2] if len(shipping_parts) > 2 else ''

    full_name = (invoice.customer_name if invoice else '') or (order.customer.name if order.customer else 'Guest Customer')
    name_parts = full_name.split(' ', 1)
    first_name = name_parts[0] if name_parts else full_name
    last_name = name_parts[1] if len(name_parts) > 1 else ''

    subtotal = float(invoice.subtotal) if invoice else sum(item['price'] * item['quantity'] for item in order_items)
    shipping_cost = float(invoice.shipping_cost) if invoice else max(0.0, float(order.total_amount) - subtotal + float(order.discount_amount or 0))
    total_amount = float(invoice.total_amount) if invoice else float(order.total_amount)

    order_view = SimpleNamespace(
        id=order.id,
        order_id=order.order_number,
        order_number=order.order_number,
        order_date=order.created_at.isoformat() if order.created_at else '',
        status=order.status,  # ✅ NEW: Pass actual order status
        items=order_items,
        order_summary=SimpleNamespace(
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            tax_amount=0,
            total=total_amount,
            discount_amount=float(order.discount_amount or 0),  # ✅ NEW: Pass discount amount
            coupon_code=order.coupon_code,  # ✅ NEW: Pass coupon code if applied
        ),
        customer_info=SimpleNamespace(
            first_name=first_name,
            last_name=last_name,
            email=(invoice.customer_email if invoice else '') or (order.customer.email if order.customer else ''),
            phone=(invoice.customer_phone if invoice else '') or (order.customer.phone if order.customer else ''),
            shipping_address=SimpleNamespace(
                street=street,
                city=city,
                state='',
                zip_code='',
                country=country,
            ),
        ),
    )

    return render_template(
        'frontside/checkout/order_confirmation.html',
        title=f"Order Confirmation - {order.order_number}",
        order=order_view
    )


@checkout_bp.route('/invoice/<int:order_id>')
def view_invoice(order_id):
    """View invoice for an order"""
    from model.invoice import Invoice
    
    order = Order.query.get(order_id)
    if not order:
        flash('Order not found', 'error')
        return redirect(url_for('shop.shop'))
    
    # Verify authorization
    user_id = get_customer_session_id()
    guest_order_id = session.get('guest_order_id')
    
    if order.customer_id and order.customer_id != user_id:
        security_logger.warning(f'Unauthorized invoice access: Order {order_id} by User {user_id}')
        flash('You do not have permission to view this invoice', 'error')
        return redirect(url_for('shop.shop'))
    
    if not order.customer_id and guest_order_id != order_id:
        flash('Order not found', 'error')
        return redirect(url_for('shop.shop'))
    
    # Get invoice
    invoice = Invoice.query.filter_by(order_id=order_id).first()
    if not invoice:
        flash('Invoice not found', 'error')
        return redirect(url_for('checkout.order_confirmation', order_id=order_id))
    
    return render_template('frontside/checkout/invoice.html', 
                         title=f"Invoice - {invoice.invoice_number}",
                         invoice=invoice,
                         order=order)


@checkout_bp.route('/api/create-order', methods=['POST'])
def create_order_api():
    """
    API endpoint to create an order with customer and cart data.
    Used by Bakong payment flow to create order before QR generation.
    Returns order_id for use in payment processing.
    """
    try:
        if not request.is_json:
            return jsonify({'success': False, 'message': 'Invalid request format'}), 400
        
        data = request.get_json()
        
        # Validate cart
        cart_items = session.get('cart', [])
        if not cart_items:
            security_logger.warning(f'Empty cart order creation attempt from IP: {request.remote_addr}')
            return _safe_api_error('Cart is empty', 400)
        
        # Get payment method and validate
        payment_method = data.get('payment_method', 'credit_card').lower()
        if payment_method not in ALLOWED_PAYMENT_METHODS:
            security_logger.warning(f'Invalid payment method in order creation: {payment_method}')
            return _safe_api_error('Invalid payment method', 400)
        
        # Get currency and validate
        currency = data.get('currency', 'USD').upper()
        if currency not in ALLOWED_CURRENCIES:
            currency = 'USD'
        
        # Get customer data
        customer_id = get_customer_session_id()
        
        customer_data = _validate_checkout_customer_info(
            data.get('name'),
            data.get('email'),
            data.get('phone'),
            data.get('address'),
            data.get('city'),
            data.get('country'),
        )

        validated_items = _validate_cart_inventory(cart_items)
        
        # Calculate order
        coupon_code = session.get('coupon_code')
        include_shipping = data.get('include_shipping', True)
        if isinstance(include_shipping, str):
            include_shipping = include_shipping.lower() not in ['false', '0', 'no']
        else:
            include_shipping = bool(include_shipping)
        shipping_method = data.get('shipping')  # Get selected shipping method
        verified_cart_items = [
            {
                'id': item['product_id'],
                'price': item['unit_price'],
                'quantity': item['quantity'],
            }
            for item in validated_items
        ]
        order_summary = build_order_summary(
            verified_cart_items,
            coupon_code,
            customer_id,
            include_shipping=include_shipping,
            shipping_method=shipping_method
        )
        
        new_order, _invoice = _create_order_with_invoice(
            cart_items=cart_items,
            customer_id=customer_id,
            currency=currency,
            payment_method=payment_method,
            coupon_code=coupon_code,
            order_summary=order_summary,
            name=customer_data['name'],
            email=customer_data['email'],
            phone=customer_data['phone'],
            address=customer_data['address'],
            city=customer_data['city'],
            country=customer_data['country'],
            reserve_stock=False,
            validated_items=validated_items,
        )
        order_number = new_order.order_number
        
        # Store order info in session
        session['temp_order_id'] = new_order.id
        session['temp_order_number'] = order_number
        if customer_id is None:
            session['guest_order_id'] = new_order.id
        session.modified = True
        
        security_logger.info(f'Order created via API: {order_number} | Payment: {payment_method} | IP: {request.remote_addr}')
        
        return jsonify({
            'success': True,
            'message': 'Order created successfully',
            'order_id': new_order.id,
            'order_number': order_number,
            'amount': float(order_summary['total']),
            'currency': currency
        }), 201
        
    except ValueError as e:
        db.session.rollback()
        security_logger.warning(f'Order creation validation failed: {str(e)} | IP: {request.remote_addr}')
        return _safe_api_error(str(e), 400)
    except Exception as e:
        db.session.rollback()
        security_logger.error(f'Error creating order via API: {str(e)} | IP: {request.remote_addr}')
        return _safe_api_error('Failed to create order', 500, internal_error=e, log_prefix='CreateOrderApiError')


# ==================== BAKONG PAYMENT API ENDPOINTS ====================

@checkout_bp.route('/api/bakong/generate-qr', methods=['POST'])
def generate_bakong_qr():
    """
    Secure endpoint to generate Bakong QR codes.
    The actual Bakong token is stored securely on backend only.
    Frontend never receives the token.
    
    Security Features:
    - Token never exposed to frontend
    - Server-side QR generation
    - Transaction validation
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({'success': False, 'message': 'Invalid request format'}), 400
        
        data = request.get_json()
        order_id = data.get('order_id')
        amount = data.get('amount')
        khqr_mode = str(data.get('khqr_mode', 'dynamic')).lower()
        
        # Validate inputs
        if not order_id or not isinstance(order_id, int):
            security_logger.warning(f'Invalid order ID in QR generation: {order_id} from IP: {request.remote_addr}')
            return jsonify({'success': False, 'message': 'Invalid order ID'}), 400
        
        if amount is None or not isinstance(amount, (int, float)):
            security_logger.warning(f'Invalid amount in QR generation: {amount}')
            return jsonify({'success': False, 'message': 'Invalid amount'}), 400

        if khqr_mode not in ['dynamic', 'static']:
            return jsonify({'success': False, 'message': 'Invalid KHQR mode'}), 400
        
        # Retrieve order and validate
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'message': 'Order not found'}), 404
        
        # Verify order belongs to user (if logged in) or is guest order
        user_id = get_customer_session_id()
        guest_order_id = session.get('guest_order_id')
        
        if order.customer_id and order.customer_id != user_id:
            security_logger.warning(f'Unauthorized QR generation: Order {order_id} by User {user_id}')
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        if not order.customer_id and guest_order_id != order_id:
            security_logger.warning(f'Unauthorized guest QR generation: Order {order_id}')
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Security: Verify amount matches order total (for dynamic QR)
        # For static QR, force amount to 0 regardless of what's sent (more flexible)
        if khqr_mode == 'dynamic':
            # Dynamic QR: amount must match order total
            if abs(float(amount) - float(order.total_amount)) > 0.01:  # Allow small floating point differences
                security_logger.warning(f'Amount mismatch in QR generation: Order {order_id} | Expected: {order.total_amount} | Got: {amount}')
                return jsonify({'success': False, 'message': 'Amount mismatch'}), 400
            # Use the order total for dynamic QR
            final_amount = float(order.total_amount)
        else:  # static mode
            # Static QR: always use amount=0 regardless of what frontend sends
            final_amount = 0
        
        # Generate transaction ID and store in session
        transaction_id = f"{order.order_number}-{os.urandom(4).hex().upper()}"
        session[f'bakong_transaction_{order_id}'] = transaction_id
        session.modified = True

        # Generate KHQR payload using bakong-khqr library (works with ABA, Bakong, Wing, etc.)
        qr_payload = generate_khqr_payload(order, final_amount, mode=khqr_mode)
        
        # Generate MD5 hash from the payload (needed for payment verification)
        khqr_instance = _get_khqr()
        md5_hash = khqr_instance.generate_md5(qr_payload)
        print(f'✅ Generated MD5: {md5_hash}')
        
        # Generate QR image in the same plain PNG style as the teacher sample.
        qr_code_data_url = _generate_qr_code_data_url(qr_payload)

        # Log successful QR generation
        security_logger.info(f'Bakong QR generated for Order: {order.order_number} | Transaction: {transaction_id} | Amount: ${final_amount}')

        return jsonify({
            'success': True,
            'message': 'QR code generated successfully',
            'transaction_id': transaction_id,
            'order_id': order_id,
            'amount': float(final_amount),
            'currency': order.currency,
            'khqr_mode': khqr_mode,
            'qr_payload': qr_payload,
            'md5_hash': md5_hash,  # Return MD5 hash separately
            'qr_code_data_url': qr_code_data_url,
            'valid_for_minutes': 10  # QR code expires after 10 minutes
        }), 200
        
    except ValueError as e:
        security_logger.error(f'Invalid KHQR configuration: {str(e)} | IP: {request.remote_addr}')
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        security_logger.error(f'Error generating Bakong QR: {str(e)} | IP: {request.remote_addr}')
        return jsonify({'success': False, 'message': 'Error generating QR code'}), 500


@checkout_bp.route('/api/bakong/verify-payment', methods=['GET', 'POST'])
def verify_bakong_payment():
    """
    Verify Bakong payment status using bakong-khqr library.
    Supports both:
    1. Manual status verification (status parameter)
    2. Automatic API verification (using md5_hash if valid token configured)
    
    Accepts both GET (for polling) and POST (for webhook callbacks)
    Updates invoice and order status on successful payment.
    """
    try:
        from model.invoice import Invoice
        
        # Handle both GET (polling) and POST (webhook) requests
        if request.method == 'GET':
            data = request.args.to_dict()
        else:
            if not request.is_json:
                return jsonify({'success': False, 'message': 'Invalid request format'}), 400
            data = request.get_json()
        
        # Get parameters
        order_id = data.get('order_id')
        transaction_id = data.get('transaction_id')
        md5_hash = data.get('md5_hash')  # MD5 hash for Bakong API verification
        status = data.get('status', 'pending')  # success, failed, pending
        
        print(f'\n🔍 VERIFY PAYMENT DEBUG:')
        print(f'   Order ID: {order_id}')
        print(f'   Transaction ID: {transaction_id}')
        print(f'   MD5 Hash provided: {bool(md5_hash)}')
        print(f'   MD5 value: {md5_hash}')
        print(f'   Status: {status}')
        
        # Validate inputs
        if not order_id or not isinstance(order_id, (int, str)):
            security_logger.warning(f'Invalid order_id in verify-payment: {order_id}')
            return jsonify({'success': False, 'message': 'Invalid order ID'}), 400
        
        try:
            order_id = int(order_id)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Invalid order ID format'}), 400
        
        # Get order
        order = Order.query.get(order_id)
        if not order:
            security_logger.warning(f'Order not found for payment verification: {order_id}')
            return jsonify({'success': False, 'message': 'Order not found'}), 404
        
        # Verify user authorization
        user_id = get_customer_session_id()
        guest_order_id = session.get('guest_order_id')
        
        if order.customer_id and order.customer_id != user_id:
            security_logger.warning(f'Unauthorized payment verification: Order {order_id} by User {user_id}')
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        if not order.customer_id and guest_order_id != order_id:
            security_logger.warning(f'Guest order unauthorized verification: Order {order_id}')
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Try API verification if MD5 hash provided and token available
        verified_status = status
        print(f'\n🔐 BAKONG API CHECK:')
        print(f'   MD5 Hash available: {bool(md5_hash)}')
        print(f'   MD5 value length: {len(md5_hash) if md5_hash else 0}')
        print(f'   API Key available: {bool(BAKONG_API_KEY)}')
        print(f'   API Key length: {len(BAKONG_API_KEY) if BAKONG_API_KEY else 0}')
        print(f'   API Key is test token: {BAKONG_API_KEY == "test_token" if BAKONG_API_KEY else "N/A"}')
        
        if md5_hash and BAKONG_API_KEY and BAKONG_API_KEY != 'test_token':
            print(f'   ✅ Attempting Bakong API check...')
            try:
                khqr_instance = _get_khqr()
                print(f'   ✅ KHQR instance created')
                payment_status = khqr_instance.check_payment(md5_hash)
                print(f'   ✅ Bakong API Response: {payment_status}')
                print(f'   ✅ Response Type: {type(payment_status)}')
                verified_status = 'success' if payment_status == 'PAID' else 'pending' if payment_status == 'UNPAID' else 'failed'
                print(f'   ✅ Mapped status: {verified_status}')
                security_logger.info(f'Bakong API verification: MD5={md5_hash[:16]}... Status={payment_status} for Order {order.order_number}')
            except Exception as e:
                print(f'   ❌ Bakong API error: {str(e)}')
                print(f'   ❌ Error type: {type(e).__name__}')
                import traceback
                print(f'   ❌ Traceback: {traceback.format_exc()}')
                security_logger.warning(f'Bakong API verification failed for Order {order_id}: {str(e)}')
                # Fall back to manual status if API verification fails
                verified_status = status
        else:
            print(f'   ❌ Cannot call Bakong API - missing requirements')
            print(f'      - MD5: {bool(md5_hash)}')
            print(f'      - API Key: {bool(BAKONG_API_KEY)}')
            print(f'      - Is test token: {BAKONG_API_KEY == "test_token" if BAKONG_API_KEY else "N/A"}')
            verified_status = status
        
        # Update order and invoice based on payment confirmation
        print(f'\n📊 FINAL RESULT:')
        print(f'   Verified Status: {verified_status}')
        
        if verified_status == 'success':
            print(f'   ✅ PAYMENT SUCCESS - Updating order...')
            # Update order status
            order.status = 'completed'
            
            # Update invoice status
            invoice = Invoice.query.filter_by(order_id=order_id).first()
            if invoice:
                invoice.status = 'paid'
                invoice.paid_at = datetime.now()
                print(f'   ✅ Invoice marked as paid: {invoice.invoice_number}')
                security_logger.info(f'Invoice marked as paid: {invoice.invoice_number} | Order: {order.order_number}')
            
            db.session.commit()
            print(f'   ✅ Order saved to database')
            security_logger.info(f'Payment verified: {transaction_id or "N/A"} | Order: {order.order_number} | Status: {verified_status}')
            
            # Send Telegram notification to admin
            try:
                print(f'   📱 Sending Telegram notification...')
                from routes.integrations.telegram_service import get_telegram_notifier
                notifier = get_telegram_notifier()
                print(f'      - Notifier created: {notifier}')
                print(f'      - Customer name: {order.customer_name}')
                print(f'      - Amount: {order.total_amount}')
                result = notifier.send_payment_success(
                    order_id=order_id,
                    customer_name=order.customer_name or 'Guest Customer',  # ✅ Use customer_name field
                    amount=f"{order.total_amount:.2f}",
                    currency=order.currency or 'USD',
                    order_number=order.order_number
                )
                print(f'      - Send result: {result}')
                print(f'   ✅ Telegram notification sent')
            except Exception as e:
                print(f'   ❌ Telegram error: {str(e)}')
                import traceback
                print(f'   ❌ Traceback: {traceback.format_exc()}')
                security_logger.warning(f'Failed to send Telegram notification for Order {order_id}: {str(e)}')
            
            print(f'   ✅ RETURNING SUCCESS RESPONSE\n')
            return jsonify({
                'success': True,
                'message': 'Payment verified and processed',
                'status': verified_status,
                'order_id': order_id,
                'order_number': order.order_number
            }), 200
        
        elif verified_status == 'failed':
            print(f'   ❌ PAYMENT FAILED - Updating order...')
            order.status = 'payment_failed'
            db.session.commit()
            security_logger.warning(f'Payment verification failed: {transaction_id or "N/A"} | Order: {order.order_number}')
            
            # Send Telegram failure notification
            try:
                from routes.integrations.telegram_service import get_telegram_notifier
                notifier = get_telegram_notifier()
                notifier.send_payment_failed(
                    order_id=order_id,
                    customer_name=order.customer_name or 'Guest Customer',  # ✅ Use customer_name field
                    amount=f"{order.total_amount:.2f}",
                    reason='Payment verification failed'
                )
            except Exception as e:
                security_logger.warning(f'Failed to send Telegram failure notification for Order {order_id}: {str(e)}')
            
            print(f'   ❌ RETURNING FAILED RESPONSE\n')
            return jsonify({
                'success': False,
                'message': 'Payment failed',
                'status': verified_status
            }), 402
        
        else:  # pending
            print(f'   ⏳ PAYMENT STILL PENDING')
            security_logger.info(f'Payment verification pending: {transaction_id or "N/A"} | Order: {order.order_number}')
            
            print(f'   ⏳ RETURNING PENDING RESPONSE\n')
            return jsonify({
                'success': True,
                'message': 'Payment verification pending',
                'status': verified_status
            }), 200
        
    except Exception as e:
        security_logger.error(f'Error verifying Bakong payment: {str(e)}')
        return jsonify({'success': False, 'message': 'Verification failed'}), 500


@checkout_bp.route('/api/apply-coupon', methods=['POST'])
def apply_coupon_api():
    """
    API endpoint to validate and apply a coupon code during checkout.
    Returns discount amount if successful, error message if invalid.
    """
    try:
        if not request.is_json:
            return jsonify({'success': False, 'message': 'Invalid request format'}), 400
        
        data = request.get_json()
        coupon_code = data.get('coupon_code', '').strip()
        
        if not coupon_code:
            return jsonify({'success': False, 'message': 'Please enter a coupon code'}), 400
        
        # Get cart from session to calculate subtotal
        cart_items = session.get('cart', [])
        if not cart_items:
            return jsonify({'success': False, 'message': 'Your cart is empty'}), 400
        
        # Calculate subtotal
        subtotal = sum(item.get('price', 0) * item.get('quantity', 1) for item in cart_items)
        
        # Get customer ID
        customer_id = get_customer_session_id()
        
        # Validate coupon
        try:
            coupon_result = validate_and_calculate_coupon(
                customer_id=customer_id,
                code=coupon_code,
                subtotal=subtotal
            )
            
            # Store coupon in session for later use
            session['coupon_code'] = coupon_code
            session.modified = True
            
            app_logger.log_info(
                'CouponApplied',
                f'Coupon {coupon_code} applied with discount ${coupon_result.discount_amount:.2f}'
            )
            
            return jsonify({
                'success': True,
                'message': f'Coupon applied successfully',
                'discount_amount': f'{coupon_result.discount_amount:.2f}',
                'discount_type': coupon_result.discount.discount_type if coupon_result.discount else 'fixed'
            }), 200
            
        except CouponError as e:
            return jsonify({'success': False, 'message': str(e)}), 400
        except Exception as e:
            app_logger.log_error('CouponValidationError', str(e))
            return jsonify({'success': False, 'message': 'Failed to validate coupon'}), 400
    
    except Exception as e:
        security_logger.error(f'Error applying coupon: {str(e)}')
        return jsonify({'success': False, 'message': 'Error applying coupon'}), 500
