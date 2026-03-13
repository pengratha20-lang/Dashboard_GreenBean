from flask import Blueprint, render_template, abort, jsonify, send_file
import sqlite3
import os
from PIL import Image
from io import BytesIO

product_bp = Blueprint('product', __name__)

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), '../../', 'SU54_DB.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@product_bp.route('/product/<int:product_id>')
def product_detail(product_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Fetch single product from database
        cursor.execute('''
            SELECT p.id, p.product_name as name, p.price, p.stock, 
                   p.image, p.description, p.status,
                   c.category_name as category
            FROM product p
            JOIN category c ON p.category_id = c.id
            WHERE p.id = ? AND p.status = 'active'
        ''', (product_id,))
        
        row = cursor.fetchone()
        
        if not row:
            abort(404)
        
        product = {
            'id': row['id'],
            'name': row['name'],
            'price': row['price'],
            'stock': row['stock'],
            'category': row['category'].lower().replace(' ', ''),
            'image': row['image'],
            'description': row['description'],
            'rating': 5,
            'is_popular': False,
            'is_new': False
        }
        
        # Fetch all active products for recommendations
        cursor.execute('''
            SELECT p.id, p.product_name as name, p.price, p.stock, 
                   p.image, p.description, p.status,
                   c.category_name as category
            FROM product p
            JOIN category c ON p.category_id = c.id
            WHERE p.status = 'active'
            ORDER BY p.id
        ''')
        
        products_list = []
        for prod_row in cursor.fetchall():
            products_list.append({
                'id': prod_row['id'],
                'name': prod_row['name'],
                'price': prod_row['price'],
                'stock': prod_row['stock'],
                'category': prod_row['category'].lower().replace(' ', ''),
                'image': prod_row['image'],
                'description': prod_row['description'],
                'rating': 5,
                'is_popular': False,
                'is_new': False
            })
        
        conn.close()
        return render_template('shop/product_detail.html', 
                             title=f"Green Garden - {product['name']}", 
                             product=product, 
                             products=products_list)
    
    except Exception as e:
        print(f"Error fetching product detail: {e}")
        abort(404)


# API ENDPOINTS
@product_bp.route('/api/products', methods=['GET'])
def api_get_all_products():
    """Get all active products as JSON"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.id, p.product_name, p.price, p.stock, p.image, p.description, p.status,
                   c.category_name as category
            FROM product p
            JOIN category c ON p.category_id = c.id
            WHERE p.status = 'active'
            ORDER BY p.id
        ''')
        
        products = []
        for row in cursor.fetchall():
            products.append({
                'id': row['id'],
                'product_name': row['product_name'],
                'price': float(row['price']),
                'stock': row['stock'],
                'image': row['image'],
                'description': row['description'],
                'category': row['category'].lower().replace(' ', '')
            })
        
        conn.close()
        return jsonify({'success': True, 'data': products})
    
    except Exception as e:
        print(f"Error fetching products: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@product_bp.route('/api/products/<int:product_id>', methods=['GET'])
def api_get_product(product_id):
    """Get single product data as JSON"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.id, p.product_name, p.price, p.stock, p.image, p.description, p.status,
                   c.category_name as category
            FROM product p
            JOIN category c ON p.category_id = c.id
            WHERE p.id = ? AND p.status = 'active'
        ''', (product_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        product = {
            'id': row['id'],
            'product_name': row['product_name'],
            'price': float(row['price']),
            'stock': row['stock'],
            'image': row['image'],
            'description': row['description'],
            'category': row['category'].lower().replace(' ', '')
        }
        
        return jsonify({'success': True, 'data': product})
    
    except Exception as e:
        print(f"Error fetching product: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@product_bp.route('/api/products/<int:product_id>/image', methods=['GET'])
def api_get_product_image(product_id):
    """Serve full-size product image"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT image FROM product WHERE id = ? AND status = "active"', (product_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row or not row['image']:
            abort(404)
        
        image_path = os.path.join('static', 'images', row['image'])
        if not os.path.exists(image_path):
            abort(404)
        
        return send_file(image_path, mimetype='image/jpeg')
    
    except Exception as e:
        print(f"Error serving product image: {e}")
        abort(500)


@product_bp.route('/api/products/<int:product_id>/thumbnail', methods=['GET'])
def api_get_product_thumbnail(product_id):
    """Serve optimized thumbnail (300x300) of product image"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT image FROM product WHERE id = ? AND status = "active"', (product_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row or not row['image']:
            abort(404)
        
        image_path = os.path.join('static', 'images', row['image'])
        if not os.path.exists(image_path):
            abort(404)
        
        # Open image and create thumbnail
        try:
            img = Image.open(image_path)
            # Convert RGBA to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                bg = Image.new('RGB', img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = bg
            
            # Create thumbnail (300x300)
            img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            
            # Save to bytes
            img_io = BytesIO()
            img.save(img_io, format='JPEG', quality=85)
            img_io.seek(0)
            
            return send_file(img_io, mimetype='image/jpeg')
        except Exception as e:
            print(f"Error processing image: {e}")
            # Fallback: return original image
            return send_file(image_path, mimetype='image/jpeg')
    
    except Exception as e:
        print(f"Error serving thumbnail: {e}")
        abort(500)
