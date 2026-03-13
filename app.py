from flask import Flask, redirect, url_for, session
from flask_migrate import Migrate
import os
import config
from functools import wraps
from database import db
from datetime import timedelta

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config.from_object(config)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key_change_this_in_production'

# Session configuration
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize db with app
db.init_app(app)
migrate = Migrate(app, db)

from model import init_models
Product, Category = init_models(db)

# Import models after db is initialized
from model.user import User
from model.customer import Customer
from model.discount import Discount, DiscountProduct
from model.order import Order, OrderItem
from model.setting import Setting

# ==================== BACKEND (ADMIN) ROUTES ====================
from backend.routes.admin.auth import auth_bp
from backend.routes.admin.dashboard import dashboard_bp
from backend.routes.admin.product import product_bp
from backend.routes.admin.order import admin_bp as order_bp
from backend.routes.admin.customer import admin_bp as customer_bp
from backend.routes.admin.category import category_bp
from backend.routes.admin.discount import admin_bp as discount_bp
from backend.routes.admin.analytics import admin_bp as analytics_bp
from backend.routes.admin.setting import admin_bp as settings_bp
from backend.routes.admin.user import user_bp
from backend.routes.api.product_api import api_product_bp

# ==================== FRONTEND (CUSTOMER) ROUTES ====================
from frontend.routes.index import home_bp
from frontend.routes.about import about_bp
from frontend.routes.contact import contact_bp
from frontend.routes.service import service_bp
from frontend.routes.shop import shop_bp
from frontend.routes.cart import cart_bp
from frontend.routes.product import product_bp as front_product_bp
from frontend.routes.checkout import checkout_bp
from frontend.routes.auth import auth_bp as front_auth_bp
from frontend.routes.wishlist_routes import wishlist_bp
from frontend.routes.orders_routes import orders_bp

# ==================== REGISTER BACKEND BLUEPRINTS ====================
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(product_bp)
app.register_blueprint(order_bp)
app.register_blueprint(customer_bp)
app.register_blueprint(category_bp)
app.register_blueprint(discount_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(user_bp)
app.register_blueprint(api_product_bp)

# ==================== REGISTER FRONTEND BLUEPRINTS ====================
app.register_blueprint(home_bp)
app.register_blueprint(about_bp)
app.register_blueprint(contact_bp)
app.register_blueprint(service_bp)
app.register_blueprint(shop_bp)
app.register_blueprint(cart_bp)
app.register_blueprint(front_product_bp)
app.register_blueprint(checkout_bp)
# Note: front_auth_bp registration - check for route conflicts with backend auth_bp
# app.register_blueprint(front_auth_bp)  # Comment out if conflicts exist
app.register_blueprint(wishlist_bp)
app.register_blueprint(orders_bp)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# Main routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('admin.dashboard_route'))
    return redirect(url_for('auth.login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)