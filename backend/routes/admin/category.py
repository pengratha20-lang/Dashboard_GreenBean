from flask import render_template, Blueprint, request, redirect, url_for
from sqlalchemy import text
from auth_helper import login_required

# Create Blueprint
category_bp = Blueprint('category_module', __name__, url_prefix='')

@category_bp.route('/categories')
@login_required
def categories_route():
	rows = getCategoriesWithProductCount()
	return render_template('dashboard/categories.html', categories=rows, module_name='Categories', module_icon='fa-barcode')

@category_bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
def add_category_route():
    from app import db, Category
    
    if request.method == 'POST':
        category_name = request.form.get('category_name', '')
        description = request.form.get('description', '')
        icon = request.form.get('icon', '')
        
        if not category_name or not icon:
            return render_template('dashboard/categories_action/add_category.html',
                                 error='Category Name and Icon are required')

        new_category = Category(
            category_name = category_name,
            description = description,
            icon = icon,
        )
        try:
            db.session.add(new_category)
            db.session.commit()
            return redirect(url_for('category_module.categories_route', message='Category Added Successfully', type='success'))
        except Exception as e:
            db.session.rollback()
            return render_template('dashboard/categories_action/add_category.html',
                                 error=f'Error: {str(e)}')

    return render_template('dashboard/categories_action/add_category.html')

@category_bp.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_category_route(category_id):
    from app import db, Category
    category = Category.query.get_or_404(category_id)
    if request.method == 'POST':
        category.category_name = request.form['category_name']
        category.description = request.form['description']
        category.icon = request.form['icon']
        try:
            db.session.commit()
            return redirect(url_for('category_module.categories_route', message='Category Updated Successfully', type='success'))
        except Exception as e:
            db.session.rollback()
            return redirect(url_for('category_module.categories_route', message='Error updating Category', type='error'))
    return render_template('dashboard/categories_action/edit_category.html', category=category)

@category_bp.route('/categories/delete/<int:category_id>', methods=['POST','GET'])
@login_required
def delete_category_route(category_id):
    from app import db, Category
    category = Category.query.get_or_404(category_id)
    if not category:
        return redirect(url_for('category_module.categories_route'))
    try:
        db.session.delete(category)
        db.session.commit()
        return redirect(url_for('category_module.categories_route', message='Category Deleted Successfully', type='success'))
    except Exception as e:
        db.session.rollback()
        return redirect(url_for('category_module.categories_route', message='Error deleting Category', type='error'))

def getCategoriesWithProductCount():
    from app import db
    sql = text("""
        SELECT c.id, c.category_name,c.icon, COUNT(p.category_id) AS total_products
        FROM category c
        LEFT JOIN product p ON c.id = p.category_id
        GROUP BY c.id, c.category_name
        ORDER BY c.id
    """)
    result = db.session.execute(sql).fetchall()
    return [dict(row._mapping) for row in result]