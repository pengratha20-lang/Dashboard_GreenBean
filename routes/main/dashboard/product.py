from flask import render_template, request, redirect, url_for, Blueprint, jsonify, session
from sqlalchemy import text
from core.database import db
from model.product import Product
from model.category import Category
from model.stock_log import StockLog
import os
from datetime import datetime
from core.upload_service_enhanced import save_image_organized
from config.settings import ALLOWED_EXTENSIONS
from core.auth_helper import login_required
from core.image_helper import ImagePathHelper
from core.helpers import FormValidator, FormErrorHandler, StockManager, DataExporter, BulkOperationValidator

product_bp = Blueprint('product_module', __name__, url_prefix='')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@product_bp.route('/products')
@login_required
def products_route():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '')
    per_page = 10

    rows = getAllProductsList()
    
    # Apply search filter
    if search_query:
        search_lower = search_query.lower()
        rows = [r for r in rows if search_lower in r['product_name'].lower() or search_lower in r['category_name'].lower()]
        
    # Apply status filter
    if status_filter == 'instock':
        rows = [r for r in rows if r['stock'] > 10]
    elif status_filter == 'low':
        rows = [r for r in rows if 0 < r['stock'] <= 10]
    elif status_filter == 'out':
        rows = [r for r in rows if r['stock'] <= 0]

    total = len(rows)
    start = (page - 1) * per_page
    end = start + per_page
    products = rows[start:end]

    total_pages = (total + per_page - 1) // per_page if total > 0 else 1

    return render_template('dashboard/products.html',
                           module_name='Products', module_icon='fa-boxes',
                           module='products', products=products,
                           page=page, total_pages=total_pages, total=total)

@product_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        # Validate form data
        errors = FormValidator.validate_product(request.form)
        if errors:
            categories = Category.query.all()
            return render_template('dashboard/products_action/add_product.html',
                                 module_name='Add Product', module_icon='fa-plus-circle',
                                 categories=categories,
                                 validation_errors=errors,
                                 form_data=request.form)

        product_name = request.form.get('product_name').strip()
        category_id = request.form.get('category_id')
        price = float(request.form.get('price'))
        stock = int(request.form.get('stock'))
        status = request.form.get('status', 'instock')
        description = request.form.get('description', '').strip()
        image_file = request.files.get('image')

        try:
            image_filename = handle_image_upload(image_file)
        except ValueError as e:
            categories = Category.query.all()
            return render_template('dashboard/products_action/add_product.html',
                                 module_name='Add Product', module_icon='fa-plus-circle',
                                 categories=categories,
                                 validation_errors={'image': str(e)},
                                 form_data=request.form)

        new_product = Product(
            product_name=product_name,
            category_id=int(category_id),
            price=price,
            stock=stock,
            status=status,
            description=description,
            image=image_filename
        )
        try:
            db.session.add(new_product)
            db.session.flush()  # Get the product ID
            
            # Log stock change
            StockLog.create_entry(
                product_id=new_product.id,
                change_type='initial',
                quantity_before=0,
                quantity_change=stock,
                quantity_after=stock,
                note='Product created'
            )
            
            db.session.commit()
            return redirect(url_for('product_module.products_route',
                                    message='Product created successfully!', type='success'))
        except Exception as e:
            db.session.rollback()
            error_info = FormErrorHandler.get_user_friendly_error(str(e))
            categories = Category.query.all()
            return render_template('dashboard/products_action/add_product.html',
                                 module_name='Add Product', module_icon='fa-plus-circle',
                                 categories=categories,
                                 error_info=error_info,
                                 form_data=request.form)

    categories = Category.query.all()
    return render_template('dashboard/products_action/add_product.html',
                           module_name='Add Product', module_icon='fa-plus-circle',
                           categories=categories)

@product_bp.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.query.get(product_id)

    if not product:
        return redirect(url_for('product_module.products_route',
                               message='Product not found', type='error'))

    if request.method == 'POST':
        # Validate form data
        errors = FormValidator.validate_product(request.form)
        if errors:
            categories = Category.query.all()
            return render_template('dashboard/products_action/edit_product.html',
                                 product=product, categories=categories,
                                 module_name='Edit Product', module_icon='fa-edit',
                                 validation_errors=errors,
                                 form_data=request.form)

        old_stock = product.stock
        new_stock = int(request.form.get('stock'))
        
        product.product_name = request.form.get('product_name').strip()
        product.category_id = int(request.form.get('category_id'))
        product.price = float(request.form.get('price'))
        product.stock = new_stock
        product.status = request.form.get('status', 'instock')
        product.description = request.form.get('description', '').strip()
        
        old_image_filename = product.image
        uploaded_image_filename = None
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            try:
                uploaded_image_filename = handle_image_upload(image_file)
            except ValueError as e:
                categories = Category.query.all()
                return render_template('dashboard/products_action/edit_product.html',
                                     product=product, categories=categories,
                                     module_name='Edit Product', module_icon='fa-edit',
                                     validation_errors={'image': str(e)},
                                     form_data=request.form)
            product.image = uploaded_image_filename

        try:
            # Log stock change if different
            if old_stock != new_stock:
                StockLog.create_entry(
                    product_id=product_id,
                    change_type='adjustment',
                    quantity_before=old_stock,
                    quantity_change=new_stock - old_stock,
                    quantity_after=new_stock,
                    note='Stock adjusted via edit'
                )
            
            db.session.commit()
            if uploaded_image_filename and old_image_filename and old_image_filename != uploaded_image_filename:
                delete_image_files(old_image_filename)
            return redirect(url_for('product_module.edit_product',
                                    product_id=product_id,
                                    message='Product updated successfully!',
                                    type='success'))
        except Exception as e:
            db.session.rollback()
            if uploaded_image_filename:
                delete_image_files(uploaded_image_filename)
            error_info = FormErrorHandler.get_user_friendly_error(str(e))
            categories = Category.query.all()
            return render_template('dashboard/products_action/edit_product.html',
                                 product=product, categories=categories,
                                 module_name='Edit Product', module_icon='fa-edit',
                                 error_info=error_info,
                                 form_data=request.form)

    categories = Category.query.all()
    return render_template('dashboard/products_action/edit_product.html',
                           product=product, categories=categories,
                           module_name='Edit Product', module_icon='fa-edit')

@product_bp.route('/products/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get(product_id)

    if not product:
        return redirect(url_for('product_module.products_route',
                               message='Product not found', type='error'))

    try:
        # Keep order history intact: do not allow deleting products that already appear in orders.
        if product.order_items:
            return redirect(url_for('product_module.products_route',
                                   message='Cannot delete product linked to existing orders. Set it inactive instead.',
                                   type='error'))

        # Remove stock log children first to avoid foreign key constraint errors.
        StockLog.query.filter_by(product_id=product.id).delete()

        delete_image_files(product.image)
        db.session.delete(product)
        db.session.commit()
        return redirect(url_for('product_module.products_route',
                                message='Product deleted successfully!', type='success'))
    except Exception as e:
        db.session.rollback()
        error_info = FormErrorHandler.get_user_friendly_error(str(e))
        return redirect(url_for('product_module.products_route',
                                message=f"Error: {error_info.get('message', 'Failed to delete product')}", type='error'))


# ============ BULK OPERATIONS ============
@product_bp.route('/products/bulk-delete', methods=['POST'])
@login_required
def bulk_delete_products():
    """Bulk delete multiple products"""
    product_ids = request.json.get('ids', [])
    
    # Validate
    validation = BulkOperationValidator.validate_bulk_delete(product_ids, max_count=50)
    if not validation['success']:
        return jsonify({'success': False, 'error': validation['error']}), 400
    
    try:
        products = Product.query.filter(Product.id.in_(product_ids)).all()
        deleted_count = 0
        blocked_count = 0
        blocked_names = []
        
        for product in products:
            if product.order_items:
                blocked_count += 1
                blocked_names.append(product.product_name)
                continue

            StockLog.query.filter_by(product_id=product.id).delete()
            delete_image_files(product.image)
            db.session.delete(product)
            deleted_count += 1
        
        db.session.commit()

        message = f'Successfully deleted {deleted_count} product(s)'
        if blocked_count:
            message += f'. {blocked_count} skipped due to order history.'

        return jsonify({
            'success': True,
            'message': message,
            'deleted_count': deleted_count,
            'blocked_count': blocked_count,
            'blocked_products': blocked_names
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@product_bp.route('/products/bulk-update-status', methods=['POST'])
@login_required
def bulk_update_status():
    """Bulk update product status"""
    product_ids = request.json.get('ids', [])
    new_status = request.json.get('status', '')
    
    validation = BulkOperationValidator.validate_bulk_update(product_ids, {'status': new_status}, max_count=50)
    if not validation['success']:
        return jsonify({'success': False, 'error': validation['error']}), 400
    
    try:
        products = Product.query.filter(Product.id.in_(product_ids)).all()
        for product in products:
            product.status = new_status
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Updated {len(products)} product(s) status to {new_status}',
            'updated_count': len(products)
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@product_bp.route('/products/export', methods=['POST'])
@login_required
def export_products():
    """Export products to CSV"""
    from flask import make_response
    
    products = Product.query.all()
    export_data = DataExporter.prepare_product_export(products)
    columns = ['Product Name', 'Category', 'Price', 'Stock', 'Status', 'Created']
    
    csv_content = DataExporter.export_to_csv(export_data, columns)
    
    response = make_response(csv_content)
    response.headers['Content-Disposition'] = 'attachment; filename=products.csv'
    response.headers['Content-Type'] = 'text/csv'
    
    return response

def getAllProductsList():
    sql = text("""SELECT p.*, c.category_name FROM product p INNER JOIN category c ON c.id = p.category_id;""")
    result = db.session.execute(sql).fetchall()
    rows = [dict(row._mapping) for row in result]

    for row in rows:
        image_name = row.get('image')
        if image_name:
            row['thumbnail_url'] = ImagePathHelper.get_url_path('product', image_name, 'thumbnail')
        else:
            row['thumbnail_url'] = None

        updated_at = row.get('update_at')
        image_version = 0
        if updated_at:
            if hasattr(updated_at, 'timestamp'):
                image_version = int(updated_at.timestamp())
            elif isinstance(updated_at, str):
                try:
                    image_version = int(datetime.fromisoformat(updated_at.replace('Z', '+00:00')).timestamp())
                except ValueError:
                    image_version = int(datetime.now().timestamp())

        row['image_version'] = image_version

    return rows

def handle_image_upload(image_file):
    """Handle image upload and return filename or None"""
    if not image_file or not image_file.filename:
        return None
    if not allowed_file(image_file.filename):
        allowed_exts = ', '.join(sorted(ALLOWED_EXTENSIONS))
        raise ValueError(f'Invalid image format. Allowed: {allowed_exts}')
    try:
        result = save_image_organized(image_file, 'product')
        if isinstance(result, dict):
            return result['original']
        raise ValueError('Failed to upload image')
    except Exception as e:
        print(f"Image upload error: {e}")
        raise ValueError('Failed to upload image')

def delete_image_files(image_filename):
    """Delete all image variants from organized structure"""
    if not image_filename or image_filename == 'default.png':
        return
    try:
        ImagePathHelper.delete_all_versions('product', image_filename)
    except Exception as e:
        print(f"Could not delete image files for {image_filename}: {e}")
