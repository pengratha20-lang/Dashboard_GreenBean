from flask import Blueprint, render_template
import sqlite3
import os

shop_bp = Blueprint('shop', __name__)

VALID_CATEGORY_FILTERS = {'indoor', 'outdoor', 'pot', 'accessories'}

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), '../../', 'SU54_DB.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def normalize_category_key(raw_category):
    category_key = (raw_category or '').lower().replace(' ', '')
    if 'indoor' in category_key:
        return 'indoor'
    if 'outdoor' in category_key:
        return 'outdoor'
    if 'pot' in category_key or 'planter' in category_key:
        return 'pot'
    if 'accessories' in category_key or 'accessory' in category_key:
        return 'accessories'
    return ''


def fetch_all_active_products_and_counts():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.id, p.product_name as name, p.price, p.stock,
               p.image, p.description, p.status,
               c.category_name as category
        FROM product p
        JOIN category c ON p.category_id = c.id
        WHERE p.status = 'active'
        ORDER BY p.id
    ''')

    products = []
    category_counts = {
        'total': 0,
        'indoor': 0,
        'outdoor': 0,
        'pot': 0,
        'accessories': 0
    }

    for row in cursor.fetchall():
        category_short = normalize_category_key(row['category'])
        products.append({
            'id': row['id'],
            'name': row['name'],
            'price': row['price'],
            'stock': row['stock'],
            'category': category_short,
            'image': row['image'],
            'description': row['description'],
            'rating': 5,
            'is_popular': False,
            'is_new': False,
            'is_on_sale': False
        })

        category_counts['total'] += 1
        if category_short in category_counts:
            category_counts[category_short] += 1

    conn.close()
    return products, category_counts

@shop_bp.route('/shop')
@shop_bp.route('/products')
def shop():
    try:
        products, category_counts = fetch_all_active_products_and_counts()
        return render_template(
            'shop/all_product.html',
            title="Green Garden - Shop",
            products=products,
            product_counts=category_counts,
            category_filter='all'
        )
    except Exception as e:
        print(f"Error fetching products: {e}")
        products = []
        category_counts = {'total': 0, 'indoor': 0, 'outdoor': 0, 'pot': 0, 'accessories': 0}
        return render_template(
            'shop/all_product.html',
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
            'shop/all_product.html',
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
            'shop/all_product.html',
            title="Green Garden - Shop",
            products=products,
            product_counts=category_counts,
            category_filter='all'
        )
