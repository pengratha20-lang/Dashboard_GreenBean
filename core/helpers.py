"""
Helper utilities for Dashboard - Error handling, validation, and common operations
"""
from functools import wraps
from flask import jsonify, session, request
from datetime import datetime, timedelta
import json

# ============ ERROR HANDLING ============

class ValidationError(Exception):
    """Custom validation error with user-friendly message"""
    def __init__(self, field, message, suggestion=None):
        self.field = field
        self.message = message
        self.suggestion = suggestion or ""
        super().__init__(self.message)

class FormErrorHandler:
    """Handle form errors with user-friendly messages"""
    
    FRIENDLY_ERRORS = {
        'UNIQUE constraint failed': {
            'field': 'product_name',
            'message': 'This product name already exists. Please use a different name.',
            'suggestion': 'Try adding a size, color, or variant to make it unique.'
        },
        'NOT NULL constraint failed': {
            'message': 'Some required fields are missing or empty.',
            'suggestion': 'Please fill in all fields marked with * (asterisk).'
        },
        'column product_name is not NULL': {
            'field': 'product_name',
            'message': 'Product name is required and cannot be empty.',
            'suggestion': 'Please enter a valid product name.'
        },
        'column price is not NULL': {
            'field': 'price',
            'message': 'Price is required.',
            'suggestion': 'Please enter a valid price (e.g., 19.99).'
        },
        'column stock is not NULL': {
            'field': 'stock',
            'message': 'Stock quantity is required.',
            'suggestion': 'Please enter the number of items in stock.'
        },
        'column category_id is not NULL': {
            'field': 'category_id',
            'message': 'Please select a category for this product.',
            'suggestion': 'Choose from the category dropdown or create a new category.'
        },
        'invalid literal for int()': {
            'message': 'Some values are in the wrong format.',
            'suggestion': 'Make sure numbers are entered without letters or special characters.'
        }
    }
    
    @staticmethod
    def get_user_friendly_error(error_message):
        """Convert technical error to user-friendly message"""
        error_str = str(error_message).lower()
        
        for error_key, error_info in FormErrorHandler.FRIENDLY_ERRORS.items():
            if error_key.lower() in error_str:
                return {
                    'title': 'Validation Error',
                    'field': error_info.get('field'),
                    'message': error_info.get('message'),
                    'suggestion': error_info.get('suggestion', ''),
                    'technical': str(error_message)
                }
        
        # Default generic error
        return {
            'title': 'Something went wrong',
            'message': 'We encountered an issue processing your request.',
            'suggestion': 'Please check your entries and try again. If the problem persists, contact support.',
            'technical': str(error_message)
        }


# ============ FORM VALIDATION ============

class FormValidator:
    """Validate form inputs with detailed error messages"""
    
    @staticmethod
    def validate_product(form_data):
        """Validate product form data"""
        errors = {}
        
        # Product name
        name = form_data.get('product_name', '').strip()
        if not name:
            errors['product_name'] = 'Product name is required'
        elif len(name) < 2:
            errors['product_name'] = 'Product name must be at least 2 characters'
        elif len(name) > 80:
            errors['product_name'] = 'Product name cannot exceed 80 characters'
        
        # Category
        category_id = form_data.get('category_id', '').strip()
        if not category_id:
            errors['category_id'] = 'Please select a category'
        
        # Price
        price = form_data.get('price', '').strip()
        if not price:
            errors['price'] = 'Price is required'
        else:
            try:
                price_val = float(price)
                if price_val < 0:
                    errors['price'] = 'Price cannot be negative'
                elif price_val > 999999.99:
                    errors['price'] = 'Price is too large'
            except ValueError:
                errors['price'] = 'Price must be a valid number (e.g., 19.99)'
        
        # Stock
        stock = form_data.get('stock', '').strip()
        if not stock:
            errors['stock'] = 'Stock quantity is required'
        else:
            try:
                stock_val = int(stock)
                if stock_val < 0:
                    errors['stock'] = 'Stock cannot be negative'
                elif stock_val > 999999:
                    errors['stock'] = 'Stock quantity is too large'
            except ValueError:
                errors['stock'] = 'Stock must be a whole number'
        
        # Description
        description = form_data.get('description', '').strip()
        if description and len(description) > 500:
            errors['description'] = 'Description cannot exceed 500 characters'
        
        return errors
    
    @staticmethod
    def validate_customer(form_data):
        """Validate customer form data"""
        errors = {}
        
        name = form_data.get('name', '').strip()
        if not name:
            errors['name'] = 'Name is required'
        elif len(name) < 2:
            errors['name'] = 'Name must be at least 2 characters'
        
        email = form_data.get('email', '').strip()
        if not email:
            errors['email'] = 'Email is required'
        elif '@' not in email:
            errors['email'] = 'Please enter a valid email address'
        
        phone = form_data.get('phone', '').strip()
        if phone and len(phone) < 6:
            errors['phone'] = 'Phone number appears incomplete'
        
        return errors
    
    @staticmethod
    def validate_category(form_data):
        """Validate category form data"""
        errors = {}
        
        name = form_data.get('category_name', '').strip()
        if not name:
            errors['category_name'] = 'Category name is required'
        elif len(name) < 2:
            errors['category_name'] = 'Category name must be at least 2 characters'
        
        icon = form_data.get('icon', '').strip()
        if not icon:
            errors['icon'] = 'Please select an icon'
        
        return errors


# ============ SESSION MANAGEMENT ============

class SessionWarning:
    """Manage session timeout warnings"""
    
    # Session timeout warning threshold (15 minutes before actual timeout)
    WARNING_THRESHOLD_MINUTES = 15
    
    @staticmethod
    def get_session_info():
        """Get current session info including time remaining"""
        if 'user_id' not in session:
            return None
        
        login_time = session.get('login_time')
        if not login_time:
            return None
        
        # Parse login time
        try:
            login_dt = datetime.fromisoformat(login_time)
        except:
            return None
        
        # Calculate time remaining (assuming 1 hour session)
        now = datetime.now()
        elapsed = (now - login_dt).total_seconds() / 60
        remaining_minutes = 60 - elapsed
        
        return {
            'remaining_minutes': max(0, int(remaining_minutes)),
            'remaining_seconds': max(0, int(remaining_minutes * 60)),
            'show_warning': remaining_minutes <= SessionWarning.WARNING_THRESHOLD_MINUTES,
            'is_expired': remaining_minutes <= 0
        }
    
    @staticmethod
    def inject_session_info():
        """Inject session info into all template contexts"""
        return SessionWarning.get_session_info()


# ============ EXPORT UTILITIES ============

class DataExporter:
    """Export data to various formats"""
    
    @staticmethod
    def export_to_csv(data, columns, filename=None):
        """Export data list to CSV format
        
        Args:
            data: List of dictionaries
            columns: List of column names to export
            filename: Optional filename
        
        Returns:
            CSV string
        """
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        
        for row in data:
            writer.writerow({col: row.get(col, '') for col in columns})
        
        return output.getvalue()
    
    @staticmethod
    def prepare_order_export(orders):
        """Prepare orders data for export"""
        data = []
        for order in orders:
            data.append({
                'Order #': order.order_number,
                'Customer': order.customer.name if order.customer else 'Guest',
                'Email': order.customer.email if order.customer else 'N/A',
                'Total': f'{order.currency or "USD"} {order.total_amount}',
                'Status': order.status.capitalize(),
                'Date': order.created_at.strftime('%Y-%m-%d %H:%M') if order.created_at else 'N/A',
                'Items': len(order.items) if order.items else 0
            })
        return data
    
    @staticmethod
    def prepare_product_export(products):
        """Prepare products data for export"""
        data = []
        for product in products:
            data.append({
                'Product Name': product.product_name,
                'Category': product.category.category_name if product.category else 'N/A',
                'Price': f'${product.price:.2f}',
                'Stock': product.stock,
                'Status': product.status,
                'Created': product.create_at.strftime('%Y-%m-%d') if product.create_at else 'N/A'
            })
        return data


# ============ STOCK MANAGEMENT ============

class StockManager:
    """Manage product stock and prevent overselling"""
    
    LOW_STOCK_THRESHOLD = 10  # Alert when stock <= 10
    CRITICAL_STOCK_THRESHOLD = 0  # Alert when stock <= 0
    
    @staticmethod
    def check_stock_availability(product_id, quantity):
        """Check if product has sufficient stock
        
        Returns: dict with success, available, shortage
        """
        from model.product import Product
        
        product = Product.query.get(product_id)
        if not product:
            return {'success': False, 'error': 'Product not found'}
        
        if product.stock < quantity:
            return {
                'success': False,
                'available': product.stock,
                'shortage': quantity - product.stock,
                'error': f'Only {product.stock} items available'
            }
        
        return {'success': True, 'available': product.stock}
    
    @staticmethod
    def reserve_stock(product_id, quantity):
        """Reserve stock for an order"""
        from model.product import Product
        
        product = Product.query.get(product_id)
        if not product:
            return {'success': False, 'error': 'Product not found'}
        
        if product.stock < quantity:
            return {
                'success': False,
                'error': f'Insufficient stock. Only {product.stock} available'
            }
        
        product.stock -= quantity
        return {'success': True}
    
    @staticmethod
    def get_stock_status(stock_level):
        """Get stock status badge"""
        if stock_level <= 0:
            return 'out-of-stock'
        elif stock_level <= StockManager.LOW_STOCK_THRESHOLD:
            return 'low-stock'
        else:
            return 'in-stock'
    
    @staticmethod
    def get_stock_alert_message(stock_level):
        """Get stock alert message"""
        if stock_level <= 0:
            return f'Out of Stock - Consider reordering'
        elif stock_level <= StockManager.LOW_STOCK_THRESHOLD:
            return f'Low Stock - Only {stock_level} items remaining'
        else:
            return f'In Stock - {stock_level} items available'


# ============ BULK OPERATIONS ============

class BulkOperationValidator:
    """Validate bulk operations"""
    
    @staticmethod
    def validate_bulk_delete(ids, max_count=100):
        """Validate bulk delete operation"""
        if not ids or len(ids) == 0:
            return {'success': False, 'error': 'Please select items to delete'}
        
        if len(ids) > max_count:
            return {'success': False, 'error': f'Cannot delete more than {max_count} items at once'}
        
        return {'success': True}
    
    @staticmethod
    def validate_bulk_update(ids, update_data, max_count=100):
        """Validate bulk update operation"""
        if not ids or len(ids) == 0:
            return {'success': False, 'error': 'Please select items to update'}
        
        if len(ids) > max_count:
            return {'success': False, 'error': f'Cannot update more than {max_count} items at once'}
        
        if not update_data or len(update_data) == 0:
            return {'success': False, 'error': 'Please specify what to update'}
        
        return {'success': True}
