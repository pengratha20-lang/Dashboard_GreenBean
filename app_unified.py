from flask import Flask, redirect, url_for, session
from flask_migrate import Migrate
import os
from jinja2 import FileSystemLoader, ChoiceLoader
import config
from functools import wraps
from database import db
from datetime import timedelta
import sys

# Determine whether to run frontend or backend
APP_MODE = os.environ.get('APP_MODE', 'backend')  # 'frontend' or 'backend'
APP_PORT = 5000 if APP_MODE == 'frontend' else 5001

# Create Flask app with custom template loader
app = Flask(__name__, static_folder='static')

# Configure Jinja to search multiple template directories based on mode
if APP_MODE == 'frontend':
    template_loaders = [
        FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates/main/frontside')),
        FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates'))
    ]
else:  # backend
    template_loaders = [
        FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates/main/dashboard')),
        FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates'))
    ]

app.jinja_loader = ChoiceLoader(template_loaders)

app.config.from_object(config)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key_change_this_in_production'

# Session configuration
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
from model.setting import Setting

# ==================== FRONTEND (CUSTOMER) ROUTES ====================
if APP_MODE == 'frontend':
    from routes.main.frontside.index import home_bp
    from routes.main.frontside.about import about_bp
    from routes.main.frontside.contact import contact_bp
    from routes.main.frontside.service import service_bp
    from routes.main.frontside.shop import shop_bp
    from routes.main.frontside.cart import cart_bp
    from routes.main.frontside.product import product_bp
    from routes.main.frontside.checkout import checkout_bp
    from routes.main.frontside.auth import auth_bp
    from routes.main.frontside.wishlist_routes import wishlist_bp
    from routes.main.frontside.orders_routes import orders_bp
    
    # Register frontend blueprints
    app.register_blueprint(home_bp)
    app.register_blueprint(about_bp)
    app.register_blueprint(contact_bp)
    app.register_blueprint(service_bp)
    app.register_blueprint(shop_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(checkout_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(wishlist_bp)
    app.register_blueprint(orders_bp)

# ==================== BACKEND (ADMIN) ROUTES ====================
else:  # backend
    from routes.main.dashboard.auth import auth_bp as admin_auth_bp
    from routes.main.dashboard.dashboard import dashboard_bp
    from routes.main.dashboard.product import product_bp as admin_product_bp
    from routes.main.dashboard.order import admin_bp as order_bp
    from routes.main.dashboard.customer import admin_bp as customer_bp
    from routes.main.dashboard.category import category_bp
    from routes.main.dashboard.discount import admin_bp as discount_bp
    from routes.main.dashboard.analytics import admin_bp as analytics_bp
    from routes.main.dashboard.setting import admin_bp as settings_bp
    from routes.main.dashboard.user import user_bp
    try:
        from routes.main.dashboard.product_api import api_product_bp
        app.register_blueprint(api_product_bp)
    except ImportError:
        pass
    
    # Register backend blueprints
    app.register_blueprint(admin_auth_bp, name='admin_auth')
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_product_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(category_bp)
    app.register_blueprint(discount_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(user_bp)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if APP_MODE == 'frontend':
                return redirect(url_for('auth.login'))
            else:
                return redirect(url_for('admin_auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# Main routes
@app.route('/')
def index():
    if APP_MODE == 'frontend':
        return redirect(url_for('home.home'))
    else:
        if 'user_id' in session:
            return redirect(url_for('dashboard.dashboard_route'))
        return redirect(url_for('admin_auth.login'))

@app.route('/logout')
def logout():
    session.clear()
    if APP_MODE == 'frontend':
        return redirect(url_for('auth.login'))
    else:
        return redirect(url_for('admin_auth.login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    app_name = "Frontend" if APP_MODE == 'frontend' else "Backend"
    print(f"\n{'='*50}")
    print(f"Starting {app_name} Application")
    print(f"Port: {APP_PORT}")
    print(f"{'='*50}\n")
    
    app.run(debug=True, port=APP_PORT, host='0.0.0.0')
