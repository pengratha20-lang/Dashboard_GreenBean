from flask import render_template, request, redirect, url_for, jsonify, Blueprint
from core.database import db
from core.auth_helper import login_required
from model.customer import Customer
from werkzeug.security import generate_password_hash
import secrets

# Create Blueprint
customer_bp = Blueprint('customer_module', __name__, url_prefix='')

@customer_bp.route('/customers')
@login_required
def customers_route():
    customers = Customer.query.all()
    customers_list = [c.to_dict() for c in customers]
    return render_template('dashboard/customers.html', customers=customers_list, module_name='Customer Management', module_icon='fa-users')

@customer_bp.route('/customers/add', methods=['POST'])
@login_required
def add_customer():
    try:
        data = request.form
        
        # Check if email already exists
        existing = Customer.query.filter_by(email=data.get('email')).first()
        if existing:
            return jsonify({'success': False, 'message': 'Email already exists'}), 400
        
        new_customer = Customer(
            name=data.get('name'),
            email=data.get('email'),
            password=generate_password_hash(secrets.token_urlsafe(12)),
            phone=data.get('phone'),
            address=data.get('address'),
            city=data.get('city'),
            country=data.get('country'),
            total_orders=0
        )
        
        db.session.add(new_customer)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Customer added successfully',
            'data': new_customer.to_dict(),
            'has_temporary_password': True
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@customer_bp.route('/customers/<int:customer_id>/edit', methods=['POST'])
@login_required
def edit_customer(customer_id):
    try:
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({'success': False, 'message': 'Customer not found'}), 404
        
        data = request.form
        
        # Check if email is taken by another customer
        if data.get('email') != customer.email:
            existing = Customer.query.filter_by(email=data.get('email')).first()
            if existing:
                return jsonify({'success': False, 'message': 'Email already exists'}), 400
        
        customer.name = data.get('name', customer.name)
        customer.email = data.get('email', customer.email)
        customer.phone = data.get('phone', customer.phone)
        customer.address = data.get('address', customer.address)
        customer.city = data.get('city', customer.city)
        customer.country = data.get('country', customer.country)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Customer updated successfully', 'data': customer.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@customer_bp.route('/customers/<int:customer_id>/delete', methods=['POST', 'DELETE'])
@login_required
def delete_customer(customer_id):
    try:
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({'success': False, 'message': 'Customer not found'}), 404
        
        db.session.delete(customer)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Customer deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400
