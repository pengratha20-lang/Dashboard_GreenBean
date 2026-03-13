from flask import render_template, request, redirect, url_for, Blueprint
from sqlalchemy import text
from functools import wraps
import os
from upload_service_enhanced import save_image_organized
import config
from auth_helper import login_required

product_bp = Blueprint('product_module', __name__, url_prefix='')

UPLOAD_FOLDER = config.UPLOAD_FOLDER
ALLOWED_EXTENSIONS = config.ALLOWED_EXTENSIONS

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@product_bp.route('/products')
@login_required
def products_route():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    rows = getAllProductsList()
    total = len(rows)
    start = (page - 1) * per_page
    end = start + per_page
    products = rows[start:end]
    
    total_pages = (total + per_page - 1) // per_page
    
    return render_template('dashboard/products.html', module_name='Products', module_icon='fa-boxes', module='products', products=products, page=page, total_pages=total_pages, total=total)

@product_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    from app import db, Product, Category, app
    
    if request.method == 'POST':
        product_name = request.form.get('product_name')
        category_id = request.form.get('category_id')
        price = request.form.get('price')
        stock = request.form.get('stock')
        status = request.form.get('status', 'instock')
        description = request.form.get('description')
        image_file = request.files.get('image')
        
        if not all([product_name, category_id, price, stock]):
            return redirect(url_for('product_module.add_product'))
        
        image_filename = handle_image_upload(image_file, app)

        new_product = Product(
            product_name=product_name,
            category_id=int(category_id),
            price=float(price),
            stock=int(stock),
            status=status,
            description=description,
            image=image_filename
        )
        try:
            db.session.add(new_product)
            db.session.commit()
            return redirect(url_for('product_module.products_route', message='Product created successfully!', type='success'))
        except Exception as e:
            db.session.rollback()
            return redirect(url_for('product_module.add_product', message='Error adding product', type='error'))
    
    from app import Category
    categories = Category.query.all()
    return render_template('dashboard/products_action/add_product.html', module_name='Add Product', module_icon='fa-plus-circle', categories=categories)

@product_bp.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    from app import db, Product, Category, app
    
    product = Product.query.get(product_id)
    
    if not product:
        return redirect(url_for('product_module.products_route'))
    
    if request.method == 'POST':
        product.product_name = request.form.get('product_name')
        product.category_id = int(request.form.get('category_id'))
        product.price = float(request.form.get('price'))
        product.stock = int(request.form.get('stock'))
        product.status = request.form.get('status', 'instock')
        product.description = request.form.get('description')
        
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            delete_image_files(product.image)
            image_filename = handle_image_upload(image_file, app)
            if image_filename:
                product.image = image_filename
        
        try:
            db.session.commit()
            return redirect(url_for('product_module.products_route', message='Product updated successfully!', type='success'))
        except Exception as e:
            db.session.rollback()
            return redirect(url_for('product_module.edit_product', product_id=product_id, message='Error updating product', type='error'))
    
    from app import Category
    categories = Category.query.all()
    return render_template('dashboard/products_action/edit_product.html', product=product, categories=categories, module_name='Edit Product', module_icon='fa-edit')

@product_bp.route('/products/delete/<int:product_id>', methods=['POST', 'GET'])
@login_required
def delete_product(product_id):
    from app import db, Product
    
    product = Product.query.get(product_id)
    
    if not product:
        return redirect(url_for('product_module.products_route'))
    
    delete_image_files(product.image)
    
    try:
        db.session.delete(product)
        db.session.commit()
        return redirect(url_for('product_module.products_route', message='Product deleted successfully!', type='success'))
    except Exception as e:
        db.session.rollback()
        return redirect(url_for('product_module.products_route', message='Error deleting product', type='error'))

def getAllProductsList():
    from app import db, Product
    sql = text("""SELECT p.*, c.category_name FROM product p INNER JOIN category c ON c.id = p.category_id;""")
    result = db.session.execute(sql).fetchall()
    return [dict(row._mapping) for row in result]

def handle_image_upload(image_file, app):
    """Handle image upload and return filename or None""" 
    if not image_file or not image_file.filename or not allowed_file(image_file.filename):
        return None
    
    try:
        filename = save_image_organized(image_file, 'product')
        return filename
    except Exception as e:
        print(f"Image upload error: {e}")
        return None

def delete_image_files(image_filename):
    """Delete all image variants from new organized structure"""
    if not image_filename or image_filename == 'default.png':
        return
    
    from image_helper import ImagePathHelper
    name, ext = os.path.splitext(image_filename)
    
    # Delete from new organized structure
    for version in ['original', 'resized', 'thumbnail']:
        if version == 'resized':
            filename = f"resized_{name}{ext}"
        elif version == 'thumbnail':
            filename = f"thumb_{name}{ext}"
        else:
            filename = image_filename
        
        path = ImagePathHelper.get_file_path('product', filename, version)
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f"Deleted: {path}")
            except Exception as e:
                print(f"Could not delete {filename}: {e}")
