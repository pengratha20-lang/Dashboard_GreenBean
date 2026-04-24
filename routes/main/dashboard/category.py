from flask import render_template, Blueprint, request, redirect, url_for
from sqlalchemy import text
from core.database import db
from model.category import Category
from core.auth_helper import login_required

# Create Blueprint
category_bp = Blueprint('category_module', __name__, url_prefix='')

CATEGORY_ICON_CHOICES = [
    ('fa-leaf', 'Leaf (Indoor Plants)'),
    ('fa-seedling', 'Seedling (New Growth)'),
    ('fa-tree', 'Tree (Outdoor Plants)'),
    ('fa-box-open', 'Box Open (Accessories)'),
    ('fa-fill-drip', 'Fill Drip (Water & Nutrients)'),
    ('fa-sun', 'Sun (Lighting)'),
]

ALLOWED_CATEGORY_ICONS = {icon for icon, _ in CATEGORY_ICON_CHOICES}


def normalize_category_icon(icon_value):
    icon_value = (icon_value or '').strip()
    if icon_value.startswith('fas '):
        icon_value = icon_value.replace('fas ', '', 1).strip()
    if icon_value.startswith('fa-solid '):
        icon_value = icon_value.replace('fa-solid ', '', 1).strip()
    return icon_value if icon_value in ALLOWED_CATEGORY_ICONS else 'fa-leaf'


@category_bp.route('/categories')
@login_required
def categories_route():
    search_query = request.args.get('search', '').strip()
    rows = getCategoriesWithProductCount()
    
    if search_query:
        search_lower = search_query.lower()
        rows = [
            r for r in rows
            if search_lower in r['category_name'].lower() or search_lower in (r.get('description') or '').lower()
        ]
        
    return render_template('dashboard/categories.html',
                           categories=rows,
                           search_query=search_query,
                           module_name='Categories',
                           module_icon='fa-barcode')

@category_bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
def add_category_route():
    if request.method == 'POST':
        category_name = request.form.get('category_name', '')
        description = request.form.get('description', '')
        icon = normalize_category_icon(request.form.get('icon', ''))

        if not category_name:
            return render_template('dashboard/categories_action/add_category.html',
                                   error='Category Name is required',
                                   icon_choices=CATEGORY_ICON_CHOICES)

        new_category = Category(
            category_name=category_name,
            description=description,
            icon=icon,
        )
        try:
            db.session.add(new_category)
            db.session.commit()
            return redirect(url_for('category_module.categories_route',
                                    message='Category Added Successfully', type='success'))
        except Exception as e:
            db.session.rollback()
            return render_template('dashboard/categories_action/add_category.html',
                                   error=f'Error: {str(e)}',
                                   icon_choices=CATEGORY_ICON_CHOICES)

    return render_template('dashboard/categories_action/add_category.html', icon_choices=CATEGORY_ICON_CHOICES)

@category_bp.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_category_route(category_id):
    category = Category.query.get_or_404(category_id)
    if request.method == 'POST':
        category.category_name = request.form['category_name']
        category.description = request.form['description']
        category.icon = normalize_category_icon(request.form['icon'])
        try:
            db.session.commit()
            return redirect(url_for('category_module.categories_route',
                                    message='Category Updated Successfully', type='success'))
        except Exception as e:
            db.session.rollback()
            return redirect(url_for('category_module.categories_route',
                                    message='Error updating Category', type='error'))
    category.icon = normalize_category_icon(category.icon)
    return render_template('dashboard/categories_action/edit_category.html', category=category, icon_choices=CATEGORY_ICON_CHOICES)

@category_bp.route('/categories/delete/<int:category_id>', methods=['POST'])
@login_required
def delete_category_route(category_id):
    category = Category.query.get_or_404(category_id)
    try:
        db.session.delete(category)
        db.session.commit()
        return redirect(url_for('category_module.categories_route',
                                message='Category Deleted Successfully', type='success'))
    except Exception as e:
        db.session.rollback()
        return redirect(url_for('category_module.categories_route',
                                message='Error deleting Category', type='error'))

def getCategoriesWithProductCount():
    sql = text("""
        SELECT c.id, c.category_name, c.description, c.icon, COUNT(p.category_id) AS total_products
        FROM category c
        LEFT JOIN product p ON c.id = p.category_id
        GROUP BY c.id, c.category_name, c.description, c.icon
        ORDER BY c.category_name
    """)
    result = db.session.execute(sql).fetchall()
    rows = [dict(row._mapping) for row in result]
    for row in rows:
        row['icon'] = normalize_category_icon(row.get('icon'))
    return rows
