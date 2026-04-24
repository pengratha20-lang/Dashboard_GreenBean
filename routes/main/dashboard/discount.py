from flask import render_template, request, jsonify, Blueprint
from core.database import db
from core.auth_helper import login_required
from model.discount import Discount
from model.order import Order
from model.customer import Customer
from datetime import datetime
from services.main.dashboard.coupons import CouponError, validate_and_calculate_coupon

# Create Blueprint
discount_bp = Blueprint('discount_module', __name__, url_prefix='')

@discount_bp.route('/discounts')
@login_required
def discounts_route():
    discounts = Discount.query.all()
    discounts_list = [d.to_dict() for d in discounts]
    return render_template('dashboard/discounts.html', discounts=discounts_list, module_name='Discount Management', module_icon='fa-tag')

@discount_bp.route('/discounts/add', methods=['POST'])
@login_required
def add_discount():
    try:
        data = request.form
        max_usage_per_customer = None
        if data.get('max_usage_per_customer'):
            try:
                max_usage_per_customer = int(data.get('max_usage_per_customer'))
            except ValueError:
                max_usage_per_customer = None
        
        # Check if code already exists
        existing = Discount.query.filter_by(code=data.get('code')).first()
        if existing:
            return jsonify({'success': False, 'message': 'Coupon code already exists'}), 400
        
        new_discount = Discount(
            code=data.get('code').upper(),
            description=data.get('description'),
            discount_type=data.get('discount_type', 'percentage'),
            discount_value=float(data.get('discount_value', 0)),
            min_purchase=float(data.get('min_purchase', 0)),
            max_usage=int(data.get('max_usage')) if data.get('max_usage') else None,
            max_usage_per_customer=max_usage_per_customer,
            expiry_date=datetime.strptime(data.get('expiry_date'), '%Y-%m-%d') if data.get('expiry_date') else None,
            status=data.get('status', 'active')
        )
        
        db.session.add(new_discount)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Discount added successfully', 'data': new_discount.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@discount_bp.route('/discounts/<int:discount_id>/edit', methods=['POST'])
@login_required
def edit_discount(discount_id):
    try:
        discount = Discount.query.get(discount_id)
        if not discount:
            return jsonify({'success': False, 'message': 'Discount not found'}), 404
        
        data = request.form

        # Parse per-customer usage limit
        max_usage_per_customer = discount.max_usage_per_customer
        if data.get('max_usage_per_customer') is not None:
            if data.get('max_usage_per_customer') == '':
                max_usage_per_customer = None
            else:
                try:
                    max_usage_per_customer = int(data.get('max_usage_per_customer'))
                except ValueError:
                    max_usage_per_customer = discount.max_usage_per_customer
        
        # Check if code is taken by another discount
        if data.get('code') != discount.code:
            existing = Discount.query.filter_by(code=data.get('code')).first()
            if existing:
                return jsonify({'success': False, 'message': 'Coupon code already exists'}), 400
        
        discount.code = data.get('code', discount.code).upper()
        discount.description = data.get('description', discount.description)
        discount.discount_type = data.get('discount_type', discount.discount_type)
        discount.discount_value = float(data.get('discount_value', discount.discount_value))
        discount.min_purchase = float(data.get('min_purchase', discount.min_purchase))
        discount.max_usage = int(data.get('max_usage')) if data.get('max_usage') else None
        discount.max_usage_per_customer = max_usage_per_customer
        if data.get('expiry_date'):
            discount.expiry_date = datetime.strptime(data.get('expiry_date'), '%Y-%m-%d')
        discount.status = data.get('status', discount.status)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Discount updated successfully', 'data': discount.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@discount_bp.route('/discounts/<int:discount_id>/delete', methods=['POST', 'DELETE'])
@login_required
def delete_discount(discount_id):
    try:
        discount = Discount.query.get(discount_id)
        if not discount:
            return jsonify({'success': False, 'message': 'Discount not found'}), 404
        
        db.session.delete(discount)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Discount deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400


@discount_bp.route('/api/apply-coupon', methods=['POST'])
def apply_coupon():
    """
    Public API for validation and previewing a coupon.
    """
    try:
        data = request.get_json(silent=True) or request.form

        code = data.get('code') or data.get('coupon_code') or ''
        customer_id = data.get('customer_id')
        subtotal = data.get('subtotal')

        result = validate_and_calculate_coupon(
            customer_id=int(customer_id) if customer_id is not None else customer_id,
            code=code,
            subtotal=subtotal,
        )

        discount = result.discount
        return jsonify({
            'success': True,
            'message': f'Coupon {discount.code} applied successfully',
            'discount_amount': result.discount_amount,
            'new_total': result.new_total,
            'coupon': {
                'id': discount.id,
                'code': discount.code,
                'description': discount.description,
                'discount_type': discount.discount_type,
                'discount_value': discount.discount_value,
                'min_purchase': discount.min_purchase,
                'max_usage': discount.max_usage,
                'usage_count': discount.usage_count,
                'max_usage_per_customer': discount.max_usage_per_customer,
                'expiry_date': discount.expiry_date.strftime('%Y-%m-%d') if discount.expiry_date else None,
                'status': discount.status,
            }
        })
    except CouponError as e:
        message = str(e)
        status_code = 404 if message == 'Customer not found' else 400
        return jsonify({'success': False, 'message': message}), status_code
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400
