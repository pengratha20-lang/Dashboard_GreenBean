from flask import Flask, redirect, url_for, session, render_template, request, jsonify
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import os
from jinja2 import FileSystemLoader, ChoiceLoader
from werkzeug.middleware.proxy_fix import ProxyFix
from config.settings import UPLOAD_FOLDER, IMAGES_FOLDER, IMAGE_TYPES, IMAGE_VERSIONS, ALLOWED_EXTENSIONS, MAX_CONTENT_LENGTH
from core.database import db
from datetime import timedelta
from dotenv import load_dotenv
from sqlalchemy import inspect
from core.auth_helper import is_admin_logged_in
from core.exceptions import ApplicationError
from core.security import app_logger, security_logger, sanitize_error_message

# Load environment variables from .env file
load_dotenv()

# Create Flask app with custom template loader
app = Flask(__name__, static_folder='static')
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# Configure Jinja to search multiple template directories
# Root is templates/main to support 'dashboard/...' and 'frontside/...' paths
template_loaders = [
    FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates/main')),
    FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates'))
]
app.jinja_loader = ChoiceLoader(template_loaders)

# Configuration
database_url = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True
}
# Use environment variable for secret key, with fallback for development
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-key-change-in-production-MUST-BE-32-CHARS-MIN')
if len(app.secret_key) < 32:
    raise ValueError('FLASK_SECRET_KEY must be at least 32 characters long for security')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['IMAGES_FOLDER'] = IMAGES_FOLDER
app.config['IMAGE_TYPES'] = IMAGE_TYPES
app.config['IMAGE_VERSIONS'] = IMAGE_VERSIONS
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Session configuration with secure defaults
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
# Render sets RENDER=true for running services
is_render = os.environ.get('RENDER', 'False').lower() == 'true'
# Set to True for HTTPS in production
default_cookie_secure = 'True' if is_render else 'False'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', default_cookie_secure).lower() == 'true'
app.config['SESSION_COOKIE_HTTPONLY'] = True
# Use Strict for maximum security
app.config['SESSION_COOKIE_SAMESITE'] = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ==================== SECURITY INITIALIZATION ====================
# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize db with app
db.init_app(app)
migrate = Migrate(app, db)

from model import init_models
Product, Category = init_models(db)

# Import models
from model.user import User
from model.customer import Customer
from model.discount import Discount, DiscountProduct
from model.order import Order, OrderItem
from model.invoice import Invoice
from model.setting import Setting
from model.cart_item import CartItem

# ==================== FRONTEND (CUSTOMER) ROUTES ====================
from routes.main.frontside.index import home_bp
from routes.main.frontside.about import about_bp
from routes.main.frontside.contact import contact_bp
from routes.main.frontside.shop import shop_bp
from routes.main.frontside.cart import cart_bp
from routes.main.frontside.product import product_bp
from routes.main.frontside.checkout import checkout_bp
from routes.main.frontside.auth import auth_bp
from routes.main.frontside.wishlist_routes import wishlist_bp
from routes.main.frontside.orders_routes import orders_bp
from routes.main.frontside.service import service_bp

# Register frontend blueprints (no prefix - these are the main site)
app.register_blueprint(home_bp)
app.register_blueprint(about_bp)
app.register_blueprint(contact_bp)
app.register_blueprint(shop_bp)
app.register_blueprint(cart_bp)
app.register_blueprint(product_bp)
app.register_blueprint(checkout_bp)
app.register_blueprint(auth_bp, name='customer_auth')
app.register_blueprint(wishlist_bp)
app.register_blueprint(orders_bp)
app.register_blueprint(service_bp)

# ==================== BACKEND (ADMIN) ROUTES ====================
from routes.main.dashboard.auth import auth_bp as admin_auth_bp
from routes.main.dashboard.dashboard import dashboard_bp
from routes.main.dashboard.product import product_bp as admin_product_bp
from routes.main.dashboard.order import order_bp
from routes.main.dashboard.customer import customer_bp
from routes.main.dashboard.category import category_bp
from routes.main.dashboard.discount import discount_bp
from routes.main.dashboard.analytics import analytics_bp
from routes.main.dashboard.setting import settings_bp
from routes.main.dashboard.user import user_bp
from routes.main.dashboard.search import search_bp


def ensure_database_ready():
    """Create any missing tables at startup to protect fresh deployments."""
    auto_create = os.environ.get('AUTO_CREATE_MISSING_TABLES', 'True').lower() == 'true'
    if not auto_create:
        return

    required_tables = {
        User.__tablename__,
        Customer.__tablename__,
        Product.__tablename__,
        Category.__tablename__,
        Order.__tablename__,
        OrderItem.__tablename__,
        Discount.__tablename__,
        DiscountProduct.__tablename__,
        Invoice.__tablename__,
        Setting.__tablename__,
        CartItem.__tablename__,
    }

    with app.app_context():
        inspector = inspect(db.engine)
        existing_tables = set(inspector.get_table_names())
        missing_tables = sorted(required_tables - existing_tables)

        if missing_tables:
            app.logger.warning(
                'Missing DB tables detected at startup: %s. Running create_all() to recover.',
                ', '.join(missing_tables)
            )
            db.create_all()


ensure_database_ready()

# Register backend blueprints with /admin prefix
app.register_blueprint(admin_auth_bp, url_prefix='/admin', name='admin_auth_page')
app.register_blueprint(dashboard_bp, url_prefix='/admin')
app.register_blueprint(admin_product_bp, url_prefix='/admin')
app.register_blueprint(order_bp, url_prefix='/admin')
app.register_blueprint(customer_bp, url_prefix='/admin')
app.register_blueprint(category_bp, url_prefix='/admin')
app.register_blueprint(discount_bp, url_prefix='/admin')
app.register_blueprint(analytics_bp, url_prefix='/admin')
app.register_blueprint(settings_bp, url_prefix='/admin')
app.register_blueprint(user_bp, url_prefix='/admin')
app.register_blueprint(search_bp, url_prefix='/admin')

# ==================== CSRF EXEMPTIONS ====================
# Exempt AJAX cart endpoints that don't need CSRF protection
from routes.main.frontside.cart import sync_cart, add_to_cart, remove_from_cart, bootstrap_cart
csrf.exempt(sync_cart)
csrf.exempt(add_to_cart)
csrf.exempt(remove_from_cart)
csrf.exempt(bootstrap_cart)

# Exempt wishlist endpoints
from routes.main.frontside.wishlist_routes import add_to_wishlist, remove_from_wishlist
csrf.exempt(add_to_wishlist)
csrf.exempt(remove_from_wishlist)

# Exempt AJAX checkout/payment endpoints
from routes.main.frontside.checkout import create_order_api, generate_bakong_qr, verify_bakong_payment, process_checkout
csrf.exempt(create_order_api)
csrf.exempt(generate_bakong_qr)
csrf.exempt(verify_bakong_payment)
csrf.exempt(process_checkout)

# Exempt auth routes (login & register) - they have their own form submission handling
from routes.main.frontside.auth import login, register, update_profile, refresh_session
csrf.exempt(login)
csrf.exempt(register)
csrf.exempt(update_profile)
csrf.exempt(refresh_session)

# Admin redirect route
@app.route('/admin')
def admin_redirect():
    """Redirect /admin to /admin/login"""
    return redirect(url_for('admin_auth_page.login'))

@app.context_processor
def inject_notifications():
    if is_admin_logged_in():
        try:
            from model.order import Order
            pending_count = Order.query.filter_by(status='pending').count()
            return dict(pending_orders_count=pending_count)
        except Exception:
            pass
    return dict(pending_orders_count=0)

# Main routes
@app.route('/')
def index():
    if is_admin_logged_in():
        return redirect(url_for('admin.dashboard_route'))
    return redirect(url_for('home.home'))


def _is_ajax_request():
    """Check if request is from AJAX/Fetch API"""
    # Check multiple indicators
    if request.is_json:
        return True
    # Check Accept header
    if 'application/json' in request.headers.get('Accept', ''):
        return True
    # Check X-Requested-With header (jQuery AJAX)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return True
    return False


def _build_error_page_context(*, code, title, icon, heading, message, helper_text):
    is_admin_path = request.path.startswith('/admin')
    is_admin_session = is_admin_logged_in()

    if is_admin_path:
        primary_href = url_for('admin.dashboard_route') if is_admin_session else url_for('admin_auth_page.login')
        primary_label = 'Back To Dashboard' if is_admin_session else 'Admin Login'
        primary_icon = 'fa-gauge-high' if is_admin_session else 'fa-right-to-bracket'
        secondary_href = url_for('home.home')
        secondary_label = 'Customer Site'
        secondary_icon = 'fa-house'
    else:
        primary_href = url_for('home.home')
        primary_label = 'Back Home'
        primary_icon = 'fa-house'
        secondary_href = url_for('shop.shop')
        secondary_label = 'Browse Shop'
        secondary_icon = 'fa-leaf'

    return {
        'title': title,
        'code': code,
        'icon': icon,
        'heading': heading,
        'message': message,
        'helper_text': helper_text,
        'primary_href': primary_href,
        'primary_label': primary_label,
        'primary_icon': primary_icon,
        'secondary_href': secondary_href,
        'secondary_label': secondary_label,
        'secondary_icon': secondary_icon,
    }


# ==================== ERROR HANDLERS ====================
@app.errorhandler(ApplicationError)
def handle_application_error(error):
    """Handle custom application errors with proper logging"""
    app_logger.log_error(
        type(error).__name__,
        error.message
    )
    
    if request.is_json:
        return jsonify({'error': error.message}), error.status_code
    
    return render_template(
        'errors/error_page.html',
        **_build_error_page_context(
            title=f'{error.status_code} - Error',
            code=error.status_code,
            icon='fa-circle-exclamation',
            heading='An Error Occurred',
            message=error.message,
            helper_text='Please check your input and try again.',
        )
    ), error.status_code


@app.errorhandler(400)
def bad_request(error):
    """Handle bad requests with error page or JSON"""
    app_logger.log_error('BadRequest', str(error))
    
    if _is_ajax_request():
        return jsonify({'error': 'Bad request', 'success': False}), 400
    
    return render_template(
        'errors/error_page.html',
        **_build_error_page_context(
            title='400 - Bad Request',
            code='400',
            icon='fa-circle-exclamation',
            heading='Bad Request',
            message='The request you sent could not be understood by the server.',
            helper_text='Please check your input and try again with valid data.',
        )
    ), 400


@app.errorhandler(403)
def forbidden(error):
    """Handle CSRF and other 403 errors"""
    app_logger.log_error('Forbidden', str(error))
    
    if _is_ajax_request():
        return jsonify({'error': 'Access denied', 'success': False}), 403
    
    return render_template(
        'errors/error_page.html',
        **_build_error_page_context(
            title='403 - Access Denied',
            code='403',
            icon='fa-lock',
            heading='Access Denied',
            message='You do not have permission to access this resource.',
            helper_text='Contact an administrator if you believe this is a mistake.',
        )
    ), 403


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle method not allowed errors"""
    app_logger.log_error('MethodNotAllowed', str(error))
    
    if _is_ajax_request():
        return jsonify({'error': 'Method not allowed', 'success': False}), 405
    
    return render_template(
        'errors/error_page.html',
        **_build_error_page_context(
            title='405 - Method Not Allowed',
            code='405',
            icon='fa-ban',
            heading='Method Not Allowed',
            message='The HTTP method used is not supported for this resource.',
            helper_text='Check the request method (GET, POST, etc.) and try again.',
        )
    ), 405


@app.errorhandler(422)
def unprocessable_entity(error):
    """Handle validation errors from WTForms or JSON"""
    app_logger.log_error('UnprocessableEntity', str(error))
    
    if _is_ajax_request():
        return jsonify({'error': 'Unprocessable entity', 'success': False}), 422
    
    return render_template(
        'errors/error_page.html',
        **_build_error_page_context(
            title='422 - Invalid Data',
            code='422',
            icon='fa-triangle-exclamation',
            heading='Invalid Input',
            message='The data you submitted could not be processed.',
            helper_text='Please check all form fields and ensure they contain valid information.',
        )
    ), 422


@app.before_request
def before_request():
    """Request validation and logging"""
    # Log API calls
    if request.endpoint and not request.path.startswith('/static'):
        app_logger.log_api_call(
            request.method,
            request.path,
            None
        )


@app.errorhandler(404)
def page_not_found(error):
    """Handle 404 errors with page or JSON"""
    if _is_ajax_request():
        return jsonify({'error': 'Resource not found', 'success': False}), 404
    
    return render_template(
        'errors/error_page.html',
        **_build_error_page_context(
            title='404 - Page Not Found',
            code='404',
            icon='fa-compass',
            heading='Page Not Found',
            message="The page you're looking for doesn't exist or may have been moved.",
            helper_text='Check the URL, head back using the right area of the app, or continue browsing from a safe page.',
        )
    ), 404


@app.errorhandler(500)
def internal_server_error(error):
    """Handle 500 internal server errors"""
    try:
        db.session.rollback()
    except Exception:
        pass
    
    app_logger.log_error('InternalServerError', str(error))
    
    if _is_ajax_request():
        return jsonify({'error': 'Internal server error', 'success': False}), 500

    return render_template(
        'errors/error_page.html',
        **_build_error_page_context(
            title='500 - Server Error',
            code='500',
            icon='fa-triangle-exclamation',
            heading='Something Went Wrong',
            message='The server hit an unexpected problem while loading this page.',
            helper_text='Please try again in a moment. If it keeps happening, this route should be checked in the logs.',
        )
    ), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    print(f"\n{'='*60}")
    print("🚀 Starting Combined Application (Frontend + Backend)")
    print(f"{'='*60}")
    print("✓ Customer Site: http://127.0.0.1:5000")
    print("✓ Admin Panel:   http://127.0.0.1:5000/admin/login")
    print(f"{'='*60}\n")
    
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    if debug_mode:
        print("⚠️  DEBUG MODE ENABLED - DO NOT USE IN PRODUCTION")
    
    app.run(debug=debug_mode, port=5000, host='0.0.0.0')
