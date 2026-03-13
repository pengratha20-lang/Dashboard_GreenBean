from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from model.wishlist import Wishlist
from database import db

wishlist_bp = Blueprint('wishlist', __name__)


@wishlist_bp.route('/wishlist')
def view_wishlist():
    """View customer's wishlist"""
    if 'user_id' not in session:
        flash('Please login to view your wishlist.', 'warning')
        return redirect(url_for('auth.login', next=url_for('wishlist.view_wishlist')))
    
    try:
        wishlist_items = Wishlist.query.filter_by(customer_id=session['user_id']).all()
        return render_template('auth/wishlist.html', title='My Wishlist - Green Bean', wishlist_items=wishlist_items)
    except Exception as e:
        flash(f'Error loading wishlist: {str(e)}', 'danger')
        return redirect(url_for('home.home'))


@wishlist_bp.route('/add-to-wishlist', methods=['POST'])
def add_to_wishlist():
    """Add item to wishlist"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        product_name = data.get('product_name')
        product_price = data.get('product_price')
        product_image = data.get('product_image')
        
        # Check if already in wishlist
        existing = Wishlist.query.filter_by(
            customer_id=session['user_id'],
            product_id=product_id
        ).first()
        
        if existing:
            return jsonify({'success': False, 'message': 'Item already in wishlist'})
        
        # Add to wishlist
        wishlist_item = Wishlist(
            customer_id=session['user_id'],
            product_id=product_id,
            product_name=product_name,
            product_price=product_price,
            product_image=product_image
        )
        
        db.session.add(wishlist_item)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Added to wishlist'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@wishlist_bp.route('/remove-from-wishlist/<int:wishlist_id>', methods=['POST'])
def remove_from_wishlist(wishlist_id):
    """Remove item from wishlist"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    try:
        wishlist_item = Wishlist.query.filter_by(
            id=wishlist_id,
            customer_id=session['user_id']
        ).first()
        
        if not wishlist_item:
            return jsonify({'success': False, 'message': 'Item not found'}), 404
        
        db.session.delete(wishlist_item)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Removed from wishlist'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
