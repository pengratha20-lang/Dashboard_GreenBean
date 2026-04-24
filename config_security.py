"""
Flask Configuration for Enhanced Payment Security
Add this to your Flask app initialization
"""

import os
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import timedelta
import logging

# Load environment variables
load_dotenv()

class PaymentSecurityConfig:
    """Enhanced security configuration for payment processing"""
    
    # ==================== BASIC FLASK CONFIG ====================
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False') == 'True'
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    
    # ==================== SESSION CONFIG ====================
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = True  # Only send cookie over HTTPS
    SESSION_COOKIE_HTTPONLY = True  # No JS access to cookie
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    
    # ==================== DATABASE CONFIG ====================
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }
    
    # ==================== PAYMENT CONFIG ====================
    # Bakong
    BAKONG_API_KEY = os.getenv('BAKONG_API_KEY')
    BAKONG_MERCHANT_ID = os.getenv('BAKONG_MERCHANT_ID', 'GREEN_BEAN')
    BAKONG_WEBHOOK_SECRET = os.getenv('BAKONG_WEBHOOK_SECRET')
    
    # Payment settings
    ALLOWED_PAYMENT_METHODS = ['credit_card', 'bakong']
    ALLOWED_CURRENCIES = ['USD', 'KHR']
    TAX_RATE = 0.08
    FREE_SHIPPING_THRESHOLD = 50.0
    
    # ==================== SECURITY CONFIG ====================
    CSRF_ENABLED = True
    CSRF_SESSION_KEY = 'csrf_token'
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True
    CSRF_COOKIE_SAMESITE = 'Strict'
    
    # ==================== LOGGING CONFIG ====================
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    SECURITY_LOG_PATH = os.getenv('SECURITY_LOG_PATH', '/var/log/greenbean/security.log')
    
    # ==================== RATE LIMITING ====================
    RATELIMIT_DEFAULT = "5000 per day"
    RATELIMIT_PAYMENT_ENDPOINT = "5 per minute"
    RATELIMIT_AUTH_ENDPOINT = "10 per minute"
    
    # ==================== SSL/TLS ====================
    FORCE_HTTPS = os.getenv('FORCE_HTTPS', 'True') == 'True'
    HSTS_MAX_AGE = 31536000  # 1 year
    PREFERRED_URL_SCHEME = 'https' if FORCE_HTTPS else 'http'


def init_security(app):
    """Initialize security features for Flask app"""
    
    # Setup security headers
    @app.after_request
    def set_security_headers(response):
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        
        # Prevent MIME sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # HSTS - Force HTTPS
        response.headers['Strict-Transport-Security'] = \
            f'max-age={PaymentSecurityConfig.HSTS_MAX_AGE}; includeSubDomains'
        
        # Content Security Policy - restricts where resources can be loaded from
        response.headers['Content-Security-Policy'] = \
            "default-src 'self'; script-src 'self' 'unsafe-inline' cdnjs.cloudflare.com cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' cdnjs.cloudflare.com cdn.jsdelivr.net; img-src 'self' data: https:; font-src 'self' cdnjs.cloudflare.com cdn.jsdelivr.net; connect-src 'self'"
        
        # Referrer policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
    
    # Setup rate limiting
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=[PaymentSecurityConfig.RATELIMIT_DEFAULT]
    )
    
    # Setup logging
    setup_logging(app)
    
    return app, limiter


def setup_logging(app):
    """Setup security logging"""
    
    # Create log directory if it doesn't exist
    log_dir = os.path.dirname(PaymentSecurityConfig.SECURITY_LOG_PATH)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Configure security logger
    security_logger = logging.getLogger('security')
    security_logger.setLevel(getattr(logging, PaymentSecurityConfig.LOG_LEVEL))
    
    # File handler for security logs
    fh = logging.FileHandler(PaymentSecurityConfig.SECURITY_LOG_PATH)
    fh.setLevel(getattr(logging, PaymentSecurityConfig.LOG_LEVEL))
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    fh.setFormatter(formatter)
    
    security_logger.addHandler(fh)
    
    return security_logger


# ==================== EXAMPLE USAGE IN app.py ====================
"""
from flask import Flask
from config_security import PaymentSecurityConfig, init_security

app = Flask(__name__)
app.config.from_object(PaymentSecurityConfig)

# Initialize security
app, limiter = init_security(app)

# Apply rate limiting to payment endpoints
@app.route('/checkout/process', methods=['POST'])
@limiter.limit(PaymentSecurityConfig.RATELIMIT_PAYMENT_ENDPOINT)
def process_checkout():
    # ... payment processing code
    pass
"""
