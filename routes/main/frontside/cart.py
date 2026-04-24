from flask import Blueprint, render_template, session, request, jsonify, url_for

from core.auth_helper import is_customer_logged_in, get_customer_session_id
from core.database import db
from model.cart_item import CartItem
from model.product import Product
from services.main.frontside.coupons import validate_and_calculate_coupon, CouponError

cart_bp = Blueprint('cart', __name__)


def _sanitize_cart_quantity(quantity):
    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return 1
    return max(1, min(quantity, 99))


def _normalize_product_id(product_id):
    try:
        return int(product_id)
    except (TypeError, ValueError):
        return None


def _serialize_product_for_cart(product, quantity):
    category = getattr(product, 'category', None)
    category_name = getattr(category, 'category_name', '') if category else ''
    return {
        'id': product.id,
        'name': product.product_name,
        'price': float(product.price),
        'quantity': _sanitize_cart_quantity(quantity),
        'image': product.get_card_image_url(),
        'description': product.description or '',
        'category': category_name,
        'inStock': product.stock > 0,
    }


def _build_guest_cart_payload(cart_items):
    """Build guest cart payload from DB so session cart always has complete product fields."""
    payload = []
    product_cache = {}

    for item in cart_items:
        product_id = _normalize_product_id(item.get('id'))
        if product_id is None:
            continue

        product = product_cache.get(product_id)
        if product is None:
            product = Product.query.get(product_id)
            product_cache[product_id] = product

        if not product or product.stock <= 0:
            continue

        quantity = min(_sanitize_cart_quantity(item.get('quantity', 1)), product.stock)
        payload.append(_serialize_product_for_cart(product, quantity))

    return payload


def _build_customer_cart(customer_id):
    cart_rows = (
        CartItem.query
        .filter_by(customer_id=customer_id)
        .all()
    )

    cart_items = []
    dirty = False

    for row in cart_rows:
        product = row.product
        if not product or product.stock <= 0:
            db.session.delete(row)
            dirty = True
            continue

        clamped_quantity = min(_sanitize_cart_quantity(row.quantity), product.stock)
        if clamped_quantity != row.quantity:
            row.quantity = clamped_quantity
            dirty = True

        cart_items.append(_serialize_product_for_cart(product, clamped_quantity))

    if dirty:
        db.session.commit()

    return cart_items


def _replace_customer_cart(customer_id, cart_items):
    existing_rows = {
        row.product_id: row
        for row in CartItem.query.filter_by(customer_id=customer_id).all()
    }

    desired_quantities = {}
    valid_products = {}

    for item in cart_items:
        product_id = _normalize_product_id(item.get('id'))
        if product_id is None:
            continue

        product = valid_products.get(product_id)
        if product is None:
            product = Product.query.get(product_id)
            valid_products[product_id] = product

        if not product or product.stock <= 0:
            continue

        quantity = min(_sanitize_cart_quantity(item.get('quantity', 1)), product.stock)
        desired_quantities[product_id] = quantity

    for product_id, row in list(existing_rows.items()):
        if product_id not in desired_quantities:
            db.session.delete(row)

    for product_id, quantity in desired_quantities.items():
        row = existing_rows.get(product_id)
        if row:
            row.quantity = quantity
        else:
            db.session.add(CartItem(
                customer_id=customer_id,
                product_id=product_id,
                quantity=quantity,
            ))

    db.session.commit()
    cart_payload = _build_customer_cart(customer_id)
    session['cart'] = cart_payload
    session.modified = True
    return cart_payload


def _merge_customer_cart(customer_id, cart_items):
    existing_rows = {
        row.product_id: row
        for row in CartItem.query.filter_by(customer_id=customer_id).all()
    }

    touched = False
    product_cache = {}

    for item in cart_items:
        product_id = _normalize_product_id(item.get('id'))
        if product_id is None:
            continue

        product = product_cache.get(product_id)
        if product is None:
            product = Product.query.get(product_id)
            product_cache[product_id] = product

        if not product or product.stock <= 0:
            continue

        incoming_quantity = _sanitize_cart_quantity(item.get('quantity', 1))
        row = existing_rows.get(product_id)
        if row:
            new_quantity = min(product.stock, row.quantity + incoming_quantity)
            if new_quantity != row.quantity:
                row.quantity = new_quantity
                touched = True
        else:
            db.session.add(CartItem(
                customer_id=customer_id,
                product_id=product_id,
                quantity=min(product.stock, incoming_quantity),
            ))
            touched = True

    if touched:
        db.session.commit()

    cart_payload = _build_customer_cart(customer_id)
    session['cart'] = cart_payload
    session.modified = True
    return cart_payload

@cart_bp.route('/cart')
def cart():
    if is_customer_logged_in():
        cart_items = _build_customer_cart(get_customer_session_id())
        session['cart'] = cart_items
        session.modified = True
    else:
        cart_items = session.get('cart', [])
    total = sum(item.get('price', 0) * item.get('quantity', 1) for item in cart_items)
    return render_template('frontside/shop/cart.html', title="Green Bean - Cart", cart_items=cart_items, total=total)

@cart_bp.route('/sync-cart', methods=['POST'])
def sync_cart():
    """Sync cart from localStorage to Flask session (persistent across browser sessions)"""
    try:
        data = request.get_json()
        cart_items = data.get('cart_items', [])
        coupon_code = data.get('coupon_code')

        if is_customer_logged_in():
            cart_items = _replace_customer_cart(get_customer_session_id(), cart_items)
        else:
            cart_items = _build_guest_cart_payload(cart_items)

        # Store in session (server-side persistence)
        session['cart'] = cart_items
        if coupon_code:
            session['coupon_code'] = coupon_code
        else:
            session.pop('coupon_code', None)

        session.modified = True
        
        return jsonify({
            'success': True, 
            'message': 'Cart synced successfully',
            'cart_count': sum(item.get('quantity', 1) for item in cart_items)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@cart_bp.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    """Validate and add item to cart - REQUIRES LOGIN for customers."""
    try:
        # Check if customer is logged in
        if not is_customer_logged_in():
            return jsonify({
                'success': False,
                'message': 'Please log in to add items to your cart',
                'redirect': url_for('customer_auth.login', _external=False),
                'requiresLogin': True
            }), 401
        
        data = request.get_json()
        product_id = data.get('id')
        quantity = int(data.get('quantity', 1))
        
        # Validate quantity
        if quantity < 1:
            return jsonify({'success': False, 'message': 'Quantity must be at least 1'}), 400
        
        # Check stock availability
        from core.database import db
        from model.product import Product
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({'success': False, 'message': 'Product not found'}), 404
        
        if product.stock < quantity:
            return jsonify({
                'success': False, 
                'message': f'Only {product.stock} items available in stock',
                'available_stock': product.stock
            }), 400
        
        if is_customer_logged_in():
            customer_id = get_customer_session_id()
            existing_item = CartItem.query.filter_by(customer_id=customer_id, product_id=product_id).first()
            if existing_item:
                new_qty = existing_item.quantity + quantity
                if new_qty > product.stock:
                    return jsonify({
                        'success': False,
                        'message': f'Total quantity would exceed available stock. Only {product.stock} available.',
                        'available_stock': product.stock
                    }), 400
                existing_item.quantity = new_qty
            else:
                db.session.add(CartItem(
                    customer_id=customer_id,
                    product_id=product_id,
                    quantity=quantity,
                ))

            db.session.commit()
            cart_items = _build_customer_cart(customer_id)
            session['cart'] = cart_items
            session.modified = True

            return jsonify({
                'success': True,
                'message': 'Item added to cart successfully',
                'is_logged_in': True,
                'cart_count': sum(item.get('quantity', 1) for item in cart_items)
            })
        else:
            return jsonify({
                'success': True,
                'message': 'Item added to guest cart successfully',
                'is_logged_in': False,
                'cart_count': quantity,
            })
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid quantity format'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@cart_bp.route('/add-to-cart-form', methods=['POST'])
def add_to_cart_form():
    """Form-based add to cart (fallback for when JavaScript is disabled)"""
    from flask import redirect, url_for, flash
    
    try:
        # Get form data
        product_id = request.form.get('id', type=int)
        quantity = request.form.get('quantity', default=1, type=int)
        redirect_to = request.form.get('redirect_to', url_for('shop.shop'))
        
        # Validate quantity
        if quantity < 1:
            flash('Quantity must be at least 1', 'error')
            return redirect(redirect_to)
        
        # Check product exists and stock
        product = Product.query.get(product_id)
        if not product:
            flash('Product not found', 'error')
            return redirect(url_for('shop.shop'))
        
        if product.stock < quantity:
            flash(f'Only {product.stock} items available in stock', 'error')
            return redirect(redirect_to)
        
        # Add to cart
        if is_customer_logged_in():
            customer_id = get_customer_session_id()
            existing_item = CartItem.query.filter_by(customer_id=customer_id, product_id=product_id).first()
            
            if existing_item:
                new_qty = existing_item.quantity + quantity
                if new_qty > product.stock:
                    flash(f'Total quantity would exceed available stock. Only {product.stock} available.', 'error')
                    return redirect(redirect_to)
                existing_item.quantity = new_qty
            else:
                db.session.add(CartItem(
                    customer_id=customer_id,
                    product_id=product_id,
                    quantity=quantity,
                ))
            
            db.session.commit()
            cart_items = _build_customer_cart(customer_id)
            session['cart'] = cart_items
            session.modified = True
        else:
            # Guest cart
            cart = session.get('cart', [])
            existing = next((item for item in cart if item.get('id') == product_id), None)
            
            if existing:
                new_qty = existing.get('quantity', 1) + quantity
                if new_qty > product.stock:
                    flash(f'Total quantity would exceed available stock. Only {product.stock} available.', 'error')
                    return redirect(redirect_to)
                existing['quantity'] = new_qty
            else:
                cart.append({
                    'id': product_id,
                    'name': product.product_name,
                    'price': float(product.price),
                    'quantity': quantity,
                    'image': product.get_card_image_url(),
                    'description': product.description or '',
                    'category': getattr(getattr(product, 'category', None), 'category_name', ''),
                    'inStock': product.stock > 0,
                })
            
            session['cart'] = cart
            session.modified = True
        
        flash(f'✅ {product.product_name} added to cart!', 'success')
        return redirect(redirect_to)
    
    except Exception as e:
        flash(f'Error adding to cart: {str(e)}', 'error')
        return redirect(url_for('shop.shop'))


@cart_bp.route('/remove-from-cart/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    if is_customer_logged_in():
        row = CartItem.query.filter_by(customer_id=get_customer_session_id(), product_id=item_id).first()
        if row:
            db.session.delete(row)
            db.session.commit()
        cart_items = _build_customer_cart(get_customer_session_id())
        session['cart'] = cart_items
    elif 'cart' in session:
        session['cart'] = [item for item in session['cart'] if item.get('id') != item_id]
        session.modified = True
        cart_items = session['cart']
    else:
        cart_items = []
    
    return jsonify({
        'success': True, 
        'message': 'Item removed from cart',
        'cart_items': cart_items,
        'cart_count': sum(item.get('quantity', 1) for item in cart_items)
    })


@cart_bp.route('/api/cart/bootstrap', methods=['POST'])
def bootstrap_cart():
    if not is_customer_logged_in():
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    data = request.get_json(silent=True) or {}
    local_cart_items = data.get('cart_items', [])
    local_owner_id = str(data.get('local_owner_id', '')).strip()
    customer_id = get_customer_session_id()
    current_owner_id = str(customer_id)
    merge_required = bool(session.pop('cart_merge_required', False))

    merged = False
    merge_allowed = local_owner_id in ['', 'guest', current_owner_id]

    if merge_required and merge_allowed and local_cart_items:
        cart_items = _merge_customer_cart(customer_id, local_cart_items)
        merged = True
    else:
        cart_items = _build_customer_cart(customer_id)
        session['cart'] = cart_items
        session.modified = True

    return jsonify({
        'success': True,
        'merged': merged,
        'owner_id': current_owner_id,
        'cart_items': cart_items,
        'cart_count': sum(item.get('quantity', 1) for item in cart_items),
    })


@cart_bp.route('/api/cart/save', methods=['POST'])
def save_customer_cart():
    if not is_customer_logged_in():
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    data = request.get_json(silent=True) or {}
    cart_items = data.get('cart_items', [])
    saved_cart = _replace_customer_cart(get_customer_session_id(), cart_items)

    return jsonify({
        'success': True,
        'cart_items': saved_cart,
        'cart_count': sum(item.get('quantity', 1) for item in saved_cart),
    })


@cart_bp.route('/api/cart/validate-coupon', methods=['POST'])
def validate_coupon():
    if not is_customer_logged_in():
        return jsonify({
            'success': False,
            'message': 'Please login first to apply a coupon.',
        }), 401

    data = request.get_json(silent=True) or {}
    coupon_code = str(data.get('coupon_code', '')).strip()
    subtotal = data.get('subtotal', 0)

    try:
        result = validate_and_calculate_coupon(
            customer_id=get_customer_session_id(),
            code=coupon_code,
            subtotal=subtotal,
        )
        return jsonify({
            'success': True,
            'coupon': {
                'code': result.discount.code,
                'description': result.discount.description or result.discount.code,
                'type': result.discount.discount_type,
                'discount': float(result.discount.discount_value),
                'discount_amount': float(result.discount_amount),
            }
        })
    except CouponError as exc:
        return jsonify({
            'success': False,
            'message': str(exc),
        }), 400
