from flask import Blueprint, jsonify, send_file, current_app
from sqlalchemy import text
import os
from image_helper import ImagePathHelper

api_product_bp = Blueprint('api_product', __name__, url_prefix='/api')

# Search products by name - MUST come BEFORE /<int:product_id> route
@api_product_bp.route('/products/search/<query>', methods=['GET'])
def search_products(query):
    """Search products by name"""
    try:
        from database import db
        
        sql = text("""
            SELECT 
                p.id, 
                p.product_name, 
                p.price, 
                p.stock, 
                p.status, 
                p.image, 
                p.description, 
                p.category_id
            FROM product p
            WHERE p.product_name LIKE :query
            ORDER BY p.product_name
        """)
        
        result = db.session.execute(sql, {'query': f'%{query}%'}).fetchall()
        
        products_data = []
        for row in result:
            product_dict = {
                'id': row[0],
                'product_name': row[1],
                'price': float(row[2]) if row[2] else 0,
                'stock': int(row[3]) if row[3] else 0,
                'status': row[4],
                'image': row[5],
                'image_url': f'/api/products/{row[0]}/image',
                'thumbnail_url': f'/api/products/{row[0]}/thumbnail'
            }
            products_data.append(product_dict)
        
        return jsonify({
            'success': True,
            'data': products_data,
            'total': len(products_data)
        }), 200
    
    except Exception as e:
        print(f"Search API Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Get all products with image URLs
@api_product_bp.route('/products', methods=['GET'])
def get_all_products():
    """Get all products with image paths and details"""
    try:
        from database import db
        
        # Query using raw SQL to avoid model import issues
        sql = text("""
            SELECT 
                p.id, 
                p.product_name, 
                p.price, 
                p.stock, 
                p.status, 
                p.image, 
                p.description, 
                p.category_id,
                c.category_name
            FROM product p
            LEFT JOIN category c ON p.category_id = c.id
            ORDER BY p.id
        """)
        
        result = db.session.execute(sql).fetchall()
        
        products_data = []
        for row in result:
            product_dict = {
                'id': row[0],
                'product_name': row[1],
                'price': float(row[2]) if row[2] else 0,
                'stock': int(row[3]) if row[3] else 0,
                'status': row[4],
                'image': row[5],
                'description': row[6],
                'category_id': row[7],
                'category_name': row[8],
                'image_url': f'/api/products/{row[0]}/image',
                'thumbnail_url': f'/api/products/{row[0]}/thumbnail'
            }
            products_data.append(product_dict)
        
        return jsonify({
            'success': True,
            'data': products_data,
            'total': len(products_data)
        }), 200
    
    except Exception as e:
        print(f"API Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Get single product by ID
@api_product_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get single product with details"""
    try:
        from database import db
        
        sql = text("""
            SELECT 
                p.id, 
                p.product_name, 
                p.price, 
                p.stock, 
                p.status, 
                p.image, 
                p.description, 
                p.category_id,
                c.category_name
            FROM product p
            LEFT JOIN category c ON p.category_id = c.id
            WHERE p.id = :id
        """)
        
        result = db.session.execute(sql, {'id': product_id}).fetchone()
        
        if not result:
            return jsonify({
                'success': False,
                'error': 'Product not found'
            }), 404
        
        product_dict = {
            'id': result[0],
            'product_name': result[1],
            'price': float(result[2]) if result[2] else 0,
            'stock': int(result[3]) if result[3] else 0,
            'status': result[4],
            'image': result[5],
            'description': result[6],
            'category_id': result[7],
            'category_name': result[8],
            'image_url': f'/api/products/{result[0]}/image',
            'thumbnail_url': f'/api/products/{result[0]}/thumbnail'
        }
        
        return jsonify({
            'success': True,
            'data': product_dict
        }), 200
    
    except Exception as e:
        print(f"API Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Get/Stream product image
@api_product_bp.route('/products/<int:product_id>/image', methods=['GET'])
def get_product_image(product_id):
    """Stream product image (resized version)"""
    try:
        from database import db
        
        sql = text("SELECT image FROM product WHERE id = :id")
        result = db.session.execute(sql, {'id': product_id}).scalar()
        
        if not result:
            # Return default image if product not found
            default_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'default.png')
            if os.path.exists(default_path):
                return send_file(default_path, mimetype='image/png')
            return jsonify({
                'success': False,
                'error': 'Image not found'
            }), 404
        
        image_filename = result
        name, ext = os.path.splitext(image_filename)
        resized_filename = f"resized_{name}{ext}"
        
        image_path = ImagePathHelper.get_file_path('product', resized_filename, 'resized')
        
        # Fallback to original if resized doesn't exist
        if not os.path.exists(image_path):
            original_path = ImagePathHelper.get_file_path('product', image_filename, 'original')
            if os.path.exists(original_path):
                image_path = original_path
            else:
                return jsonify({
                    'success': False,
                    'error': 'Image file not found'
                }), 404
        
        return send_file(image_path, mimetype='image/jpeg')
    
    except Exception as e:
        print(f"Image API Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Get product thumbnail
@api_product_bp.route('/products/<int:product_id>/thumbnail', methods=['GET'])
def get_product_thumbnail(product_id):
    """Stream product thumbnail image"""
    try:
        from database import db
        
        sql = text("SELECT image FROM product WHERE id = :id")
        result = db.session.execute(sql, {'id': product_id}).scalar()
        
        if not result:
            default_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'default.png')
            if os.path.exists(default_path):
                return send_file(default_path, mimetype='image/png')
            return jsonify({
                'success': False,
                'error': 'Image not found'
            }), 404
        
        image_filename = result
        name, ext = os.path.splitext(image_filename)
        thumb_filename = f"thumb_{name}{ext}"
        
        image_path = ImagePathHelper.get_file_path('product', thumb_filename, 'thumbnail')
        
        # Fallback to resized then original if thumbnail doesn't exist
        if not os.path.exists(image_path):
            resized_filename = f"resized_{name}{ext}"
            image_path = ImagePathHelper.get_file_path('product', resized_filename, 'resized')
        
        if not os.path.exists(image_path):
            original_path = ImagePathHelper.get_file_path('product', image_filename, 'original')
            if os.path.exists(original_path):
                image_path = original_path
            else:
                return jsonify({
                    'success': False,
                    'error': 'Image file not found'
                }), 404
        
        return send_file(image_path, mimetype='image/jpeg')
    
    except Exception as e:
        print(f"Thumbnail API Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
