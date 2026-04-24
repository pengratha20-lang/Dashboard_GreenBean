from flask import Blueprint, render_template, abort, jsonify, request
from core.database import db
from core.image_helper import ImagePathHelper
from sqlalchemy import text

product_bp = Blueprint('product', __name__)
VISIBLE_PRODUCT_STATUSES = ("active", "instock")


def fetch_product_by_id(product_id, active_only=True):
    """Fetch a single product by ID using SQLAlchemy with image URLs."""
    status_filter = "AND p.status IN ('active', 'instock')" if active_only else ""
    sql = text(f'''
        SELECT p.id, p.product_name AS name, p.price, p.stock,
               p.image, p.description, p.status,
               c.category_name AS category
        FROM product p
        JOIN category c ON p.category_id = c.id
        WHERE p.id = :id {status_filter}
    ''')
    row = db.session.execute(sql, {'id': product_id}).fetchone()
    if not row:
        return None
    row_dict = dict(row._mapping)
    
    # Build image URLs
    image_name = row_dict['image']
    image_urls = {
        'thumbnail': ImagePathHelper.get_url_path('product', image_name, 'thumbnail') if image_name else '/static/images/default-product.png',
        'card': ImagePathHelper.get_url_path('product', image_name, 'resized') if image_name else '/static/images/default-product.png',
        'original': ImagePathHelper.get_url_path('product', image_name, 'original') if image_name else '/static/images/default-product.png',
    }
    
    return {
        'id': row_dict['id'],
        'name': row_dict['name'],
        'price': row_dict['price'],
        'stock': row_dict['stock'],
        'category': (row_dict.get('category') or '').lower().replace(' ', ''),
        'image': row_dict['image'],
        'image_urls': image_urls,
        'description': row_dict['description'],
        'rating': 5,
        'is_popular': False,
        'is_new': False
    }


def fetch_all_active_products():
    """Fetch all active products using SQLAlchemy with image URLs."""
    sql = text('''
        SELECT p.id, p.product_name AS name, p.price, p.stock,
               p.image, p.description, p.status,
               c.category_name AS category
        FROM product p
        JOIN category c ON p.category_id = c.id
        WHERE p.status IN ('active', 'instock')
        ORDER BY p.id
    ''')
    rows = db.session.execute(sql).fetchall()
    products = []
    
    for r in rows:
        row_dict = dict(r._mapping)
        image_name = row_dict['image']
        image_urls = {
            'thumbnail': ImagePathHelper.get_url_path('product', image_name, 'thumbnail') if image_name else '/static/images/default-product.png',
            'card': ImagePathHelper.get_url_path('product', image_name, 'resized') if image_name else '/static/images/default-product.png',
            'original': ImagePathHelper.get_url_path('product', image_name, 'original') if image_name else '/static/images/default-product.png',
        }
        
        products.append({
            'id': row_dict['id'],
            'name': row_dict['name'],
            'price': row_dict['price'],
            'stock': row_dict['stock'],
            'category': (row_dict.get('category') or '').lower().replace(' ', ''),
            'image': row_dict['image'],
            'image_urls': image_urls,
            'description': row_dict['description'],
            'rating': 5,
            'is_popular': False,
            'is_new': False
        })
    
    return products


@product_bp.route('/product/<int:product_id>')
def product_detail(product_id):
    """Display product detail page with full-size image"""
    try:
        product = fetch_product_by_id(product_id, active_only=True)
        if not product:
            abort(404)

        import random
        products_list = fetch_all_active_products()
        # Shuffle for random related products
        random.shuffle(products_list)

        return render_template(
            'frontside/shop/product_detail.html',
            title=f"Green Garden - {product['name']}",
            product=product,
            products=products_list[:10] # Take a small subset to keep it efficient
        )
    except Exception as e:
        print(f"Error fetching product detail: {e}")
        abort(404)


@product_bp.route('/api/products/<int:product_id>/thumbnail', methods=['GET'])
def api_get_product_thumbnail(product_id):
    """Serve optimized thumbnail (300x300) of product image"""
    try:
        sql = text("SELECT image FROM product WHERE id = :id AND status IN ('active', 'instock')")
        row = db.session.execute(sql, {'id': product_id}).fetchone()
        if not row or not row[0]:
            abort(404)

        image_filename = row[0]
        # Try thumbnail from organized structure first
        from core.image_helper import ImagePathHelper
        name, ext = os.path.splitext(image_filename)
        thumb_path = ImagePathHelper.get_file_path('product', f"thumb_{name}{ext}", 'thumbnail')
        if os.path.exists(thumb_path):
            return send_file(thumb_path, mimetype='image/jpeg')

        # Fall back to original and generate thumbnail on-the-fly
        image_path = ImagePathHelper.get_file_path('product', image_filename, 'original')
        if not os.path.exists(image_path):
            image_path = os.path.join(current_app.root_path, 'static', 'main', 'frontside', 'images', image_filename)
        if not os.path.exists(image_path):
            image_path = os.path.join(current_app.root_path, 'static', 'images', image_filename)
        if not os.path.exists(image_path):
            abort(404)

        img = Image.open(image_path)
        if img.mode in ('RGBA', 'LA', 'P'):
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = bg
        img.thumbnail((300, 300), Image.Resampling.LANCZOS)
        img_io = BytesIO()
        img.save(img_io, format='JPEG', quality=85)
        img_io.seek(0)
        return send_file(img_io, mimetype='image/jpeg')

    except Exception as e:
        print(f"Error serving thumbnail: {e}")
        abort(500)


@product_bp.route('/api/product/<int:product_id>/stock', methods=['GET'])
def api_get_product_stock(product_id):
    """Get product stock information for real-time validation"""
    from flask import jsonify
    try:
        product = fetch_product_by_id(product_id, active_only=True)
        if not product:
            return jsonify({'success': False, 'message': 'Product not found'}), 404
        
        return jsonify({
            'success': True,
            'id': product['id'],
            'name': product['name'],
            'price': product['price'],
            'stock': product['stock'],
            'in_stock': product['stock'] > 0
        })
    except Exception as e:
        print(f"Error getting product stock: {e}")
        return jsonify({'success': False, 'message': 'Error fetching stock info'}), 500


@product_bp.route('/api/products/search', methods=['GET', 'POST'])
def api_search_products():
    """Search products by name or category"""
    from flask import jsonify, request
    try:
        search_query = request.args.get('q', '').strip()
        if not search_query or len(search_query) < 2:
            return jsonify({'success': False, 'message': 'Search query too short', 'results': []})
        
        # Search in product names and descriptions (fuzzy search)
        sql = text('''
            SELECT p.id, p.product_name AS name, p.price, p.stock,
                   p.image, p.description,
                   c.category_name AS category
            FROM product p
            JOIN category c ON p.category_id = c.id
            WHERE p.status IN ('active', 'instock') AND (
                p.product_name LIKE :query OR 
                p.description LIKE :query OR
                c.category_name LIKE :query
            )
            ORDER BY p.product_name
            LIMIT 20
        ''')
        
        search_param = f'%{search_query}%'
        rows = db.session.execute(sql, {'query': search_param}).fetchall()
        
        results = []
        for row in rows:
            row_dict = dict(row._mapping)
            image_name = row_dict['image']
            results.append({
                'id': row_dict['id'],
                'name': row_dict['name'],
                'price': row_dict['price'],
                'stock': row_dict['stock'],
                'category': (row_dict.get('category') or '').lower().replace(' ', ''),
                'image': ImagePathHelper.get_url_path('product', image_name, 'thumbnail') if image_name else '/static/images/default-product.png',
                'description': row_dict['description'][:100] + '...' if row_dict['description'] and len(row_dict['description']) > 100 else row_dict['description']
            })
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        })
    except Exception as e:
        print(f"Error searching products: {e}")
        return jsonify({'success': False, 'message': 'Search error'}), 500


@product_bp.route('/api/products/recommended', methods=['GET'])
def api_recommended_products():
    """Return a lightweight list of active in-stock products for cart recommendations."""
    try:
        try:
            limit = int(request.args.get('limit', 4))
        except (TypeError, ValueError):
            limit = 4
        limit = max(1, min(limit, 12))

        # Use direct working query without non-existent columns
        sql = text('''
            SELECT p.id, p.product_name AS name, p.price, p.image
            FROM product p
            WHERE p.status IN ('active', 'instock') AND p.stock > 0
            ORDER BY p.id DESC
            LIMIT :limit
        ''')
        rows = db.session.execute(sql, {'limit': limit}).fetchall()
        
        products = []
        for row in rows:
            row_dict = dict(row._mapping)
            image_name = row_dict.get('image')
            products.append({
                'id': row_dict.get('id'),
                'name': row_dict.get('name'),
                'price': float(row_dict.get('price') or 0),
                'rating': 4.5,  # Default rating
                'image': ImagePathHelper.get_url_path('product', image_name, 'resized') if image_name else '/static/images/default-product.png',
            })

        return jsonify({
            'success': True,
            'products': products,
            'count': len(products),
        })
    except Exception as e:
        print(f"Error fetching recommended products: {e}")
        return jsonify({'success': False, 'message': 'Failed to fetch recommendations'}), 500
