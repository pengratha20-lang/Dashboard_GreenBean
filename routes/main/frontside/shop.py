from flask import Blueprint, render_template
from core.database import db
from core.image_helper import ImagePathHelper
from sqlalchemy import text

shop_bp = Blueprint('shop', __name__)
VISIBLE_PRODUCT_STATUSES = ("active", "instock")

VALID_CATEGORY_FILTERS = {'indoor', 'outdoor', 'pot', 'accessories'}


def normalize_category_key(raw_category):
    """Normalize category names to match sidebar filter keys or use the actual category name"""
    category_key = (raw_category or '').lower().replace(' ', '').replace('&', '')
    
    # Try to match old plant-specific categories
    if 'indoor' in category_key:
        return 'indoor'
    if 'outdoor' in category_key:
        return 'outdoor'
    if 'pot' in category_key or 'planter' in category_key:
        return 'pot'
    if 'accessories' in category_key or 'accessory' in category_key:
        return 'accessories'
    
    # If no match, return the actual category name (for flexibility with any category)
    return raw_category.lower() if raw_category else ''


def fetch_all_active_products_and_counts():
    """Fetch all active products with dynamic counts and backend filtering."""
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
    category_counts = {
        'total': 0,
        'featured': 0,
        'new': 0,
        'sale': 0,
        'top_rated': 0
    }
    
    # Dynamic categories - will be filled from actual data
    category_keys_found = set()

    for row in rows:
        row_dict = dict(row._mapping)
        category_short = normalize_category_key(row_dict.get('category', ''))
        category_keys_found.add(category_short)
        
        image_name = row_dict['image']
        
        # Default values for fields not in current schema
        is_popular = False  # Default to false - can be added to product table later
        is_new = False  # Default to false - can be added to product table later
        original_p = None  # Default to none - can be added to product table later
        is_on_sale = False  # No sale data available
        rating = 0  # Default to 0 - can be added to product table later
        
        # Build image URLs
        image_urls = {
            'thumbnail': ImagePathHelper.get_url_path('product', image_name, 'thumbnail') if image_name else '/static/images/default-product.png',
            'card': ImagePathHelper.get_url_path('product', image_name, 'resized') if image_name else '/static/images/default-product.png',
            'original': ImagePathHelper.get_url_path('product', image_name, 'original') if image_name else '/static/images/default-product.png',
        }
        
        products.append({
            'id': row_dict['id'],
            'name': row_dict['name'],
            'price': row_dict['price'],
            'original_price': original_p,
            'stock': row_dict['stock'],
            'category': category_short,
            'image': row_dict['image'],
            'image_urls': image_urls,
            'description': row_dict['description'],
            'rating': rating,
            'is_popular': is_popular,
            'is_new': is_new,
            'is_on_sale': is_on_sale
        })
        
        # Global Counts
        category_counts['total'] += 1
        if category_short:
            if category_short not in category_counts:
                category_counts[category_short] = 0
            category_counts[category_short] += 1
            
        # Quick Link Counts
        if is_popular: category_counts['featured'] += 1
        if is_new: category_counts['new'] += 1
        if is_on_sale: category_counts['sale'] += 1
        if rating >= 4: category_counts['top_rated'] += 1
    
    # Add zero counts for categories found in data
    for cat_key in sorted(category_keys_found):
        if cat_key and cat_key not in category_counts:
            category_counts[cat_key] = 0

    return products, category_counts


@shop_bp.route('/shop')
@shop_bp.route('/products')
def shop():
    from flask import request
    try:
        active_filter = request.args.get('filter', 'all').lower()
        all_products, category_counts = fetch_all_active_products_and_counts()
        
        # Apply backend filtering if param exists
        if active_filter == 'popular' or active_filter == 'featured':
            products = [p for p in all_products if p['is_popular']]
        elif active_filter == 'new':
            products = [p for p in all_products if p['is_new']]
        elif active_filter == 'sale':
            products = [p for p in all_products if p['is_on_sale']]
        elif active_filter == 'top_rated' or active_filter == 'rating':
            products = [p for p in all_products if p['rating'] >= 4]
        else:
            products = all_products

        return render_template(
            'frontside/shop/all_product.html',
            title="Green Garden - Shop",
            products=products,
            product_counts=category_counts,
            category_filter='all',
            active_filter=active_filter
        )
    except Exception as e:
        print(f"Error fetching products: {e}")
        products = []
        category_counts = {'total': 0, 'indoor': 0, 'outdoor': 0, 'pot': 0, 'accessories': 0}
        return render_template(
            'frontside/shop/all_product.html',
            title="Green Garden - Shop",
            products=products,
            product_counts=category_counts,
            category_filter='all'
        )


@shop_bp.route('/shop/category/<category>')
def category(category):
    selected_category = (category or '').lower().strip()
    if selected_category not in VALID_CATEGORY_FILTERS:
        selected_category = 'all'

    try:
        products, category_counts = fetch_all_active_products_and_counts()
        category_names = {
            'indoor': 'Indoor Plants',
            'outdoor': 'Outdoor Plants',
            'accessories': 'Accessories',
            'pot': 'Pots & Planters'
        }
        title = "Green Garden - Shop"
        if selected_category != 'all':
            title = f"Green Garden - {category_names.get(selected_category, selected_category.title())}"

        return render_template(
            'frontside/shop/all_product.html',
            title=title,
            products=products,
            product_counts=category_counts,
            category_filter=selected_category
        )
    except Exception as e:
        print(f"Error fetching products by category: {e}")
        products = []
        category_counts = {'total': 0, 'indoor': 0, 'outdoor': 0, 'pot': 0, 'accessories': 0}
        return render_template(
            'frontside/shop/all_product.html',
            title="Green Garden - Shop",
            products=products,
            product_counts=category_counts,
            category_filter='all'
        )
