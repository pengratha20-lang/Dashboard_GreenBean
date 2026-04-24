"""
Centralized application constants to prevent hardcoding values across the codebase.
Makes maintenance easier and reduces the risk of inconsistencies.
"""

# ==================== PAYMENT CONFIGURATION ====================
PAYMENT_CONFIG = {
    'ALLOWED_METHODS': ['credit_card', 'bakong'],
    'ALLOWED_CURRENCIES': ['USD', 'KHR'],
    'TAX_RATE': 0.0,  # 0% tax rate
    'FREE_SHIPPING_THRESHOLD': 50.0,  # USD threshold for free shipping
}

# ==================== KHQR (BAKONG) CONFIGURATION ====================
KHQR_CONFIG = {
    'DEFAULT_CITY': 'PHNOM PENH',
    'DEFAULT_MCC': '5999',  # Merchant Category Code
    'COUNTRY_CODE': 'KH',
    'CURRENCY_MAP': {
        'USD': '840',
        'KHR': '116',
    },
    'STATIC_QR_MODE': 'static',
    'DYNAMIC_QR_MODE': 'dynamic',
}

# ==================== ORDER STATUS FLOW ====================
ORDER_STATUS = {
    'PENDING': 'pending',
    'PROCESSING': 'processing',
    'SHIPPED': 'shipped',
    'DELIVERED': 'delivered',
    'CANCELLED': 'cancelled',
    'REFUNDED': 'refunded',
}

# Valid status transitions
VALID_STATUS_TRANSITIONS = {
    'pending': ['processing', 'cancelled'],
    'processing': ['shipped', 'cancelled'],
    'shipped': ['delivered'],
    'delivered': ['refunded'],
    'cancelled': [],
    'refunded': [],
}

# ==================== PAYMENT STATUS ====================
PAYMENT_STATUS = {
    'PENDING': 'pending',
    'PAID': 'paid',
    'FAILED': 'failed',
    'REFUNDED': 'refunded',
}

# ==================== DISCOUNT TYPES ====================
DISCOUNT_TYPE = {
    'PERCENTAGE': 'percentage',  # e.g., 10%
    'FIXED': 'fixed',  # e.g., $5 off
}

# ==================== SESSION CONFIGURATION ====================
SESSION_CONFIG = {
    'ADMIN_SESSION_KEY': 'admin_user_id',
    'CUSTOMER_SESSION_KEY': 'customer_id',
    'GUEST_SESSION_KEY': 'guest_cart_id',
    'CART_MERGE_FLAG': 'cart_merge_required',
    'LIFETIME_HOURS': 1,
    'REMEMBER_ME_DAYS': 7,
}

# ==================== IMAGE CONFIGURATION ====================
IMAGE_CONFIG = {
    'ALLOWED_EXTENSIONS': {'jpg', 'jpeg', 'png', 'gif', 'webp'},
    'MAX_FILE_SIZE_MB': 5,  # 5MB limit per image
    'VERSIONS': {
        'thumbnail': (200, 200),
        'card': (400, 400),
        'original': None,  # Keep original size
    },
    'PATHS': {
        'product': 'static/images/product',
        'user': 'static/images/user',
        'category': 'static/images/category',
        'uploads': 'static/images/uploads',
    },
}

# ==================== PRODUCT CONFIGURATION ====================
PRODUCT_CONFIG = {
    'DEFAULT_STATUS': 'active',
    'STATUS_CHOICES': ['active', 'inactive', 'discontinued'],
    'MIN_PRICE': 0.01,
    'MAX_PRICE': 999999.99,
}

# ==================== CUSTOMER CONFIGURATION ====================
CUSTOMER_CONFIG = {
    'MIN_NAME_LENGTH': 2,
    'MAX_NAME_LENGTH': 100,
    'MIN_PASSWORD_LENGTH': 8,
}

# ==================== SECURITY CONFIGURATION ====================
SECURITY_CONFIG = {
    'MIN_SECRET_KEY_LENGTH': 32,
    'PASSWORD_MIN_LENGTH': 8,
    'PASSWORD_REQUIRE_UPPERCASE': True,
    'PASSWORD_REQUIRE_LOWERCASE': True,
    'PASSWORD_REQUIRE_DIGITS': True,
    'RATE_LIMIT_PER_MINUTE': {
        'login': 5,
        'checkout': 5,
        'api_general': 30,
    },
    'MAX_LOGIN_ATTEMPTS': 5,
    'LOCKOUT_DURATION_MINUTES': 15,
}

# ==================== AUDIT LOG CONFIGURATION ====================
AUDIT_CONFIG = {
    'LOG_ACTIONS': {
        'USER_LOGIN': 'user_login',
        'USER_LOGOUT': 'user_logout',
        'ADMIN_LOGIN': 'admin_login',
        'ADMIN_LOGOUT': 'admin_logout',
        'PRODUCT_CREATE': 'product_create',
        'PRODUCT_UPDATE': 'product_update',
        'PRODUCT_DELETE': 'product_delete',
        'ORDER_UPDATE': 'order_update',
        'CUSTOMER_CREATE': 'customer_create',
        'CUSTOMER_UPDATE': 'customer_update',
        'DISCOUNT_CREATE': 'discount_create',
        'DISCOUNT_UPDATE': 'discount_update',
        'DISCOUNT_DELETE': 'discount_delete',
        'SETTING_UPDATE': 'setting_update',
    }
}

# ==================== PAGINATION ====================
PAGINATION_CONFIG = {
    'DEFAULT_PAGE_SIZE': 10,
    'MAX_PAGE_SIZE': 100,
    'ADMIN_PAGE_SIZE': 25,
}

# ==================== ERROR MESSAGES ====================
ERROR_MESSAGES = {
    'UNAUTHORIZED': 'Unauthorized access',
    'FORBIDDEN': 'You do not have permission to perform this action',
    'NOT_FOUND': 'Resource not found',
    'INVALID_INPUT': 'Invalid input provided',
    'DATABASE_ERROR': 'A database error occurred. Please try again later.',
    'SERVER_ERROR': 'An internal server error occurred',
    'SESSION_EXPIRED': 'Your session has expired. Please log in again.',
}

# ==================== SUCCESS MESSAGES ====================
SUCCESS_MESSAGES = {
    'PRODUCT_CREATED': 'Product created successfully',
    'PRODUCT_UPDATED': 'Product updated successfully',
    'PRODUCT_DELETED': 'Product deleted successfully',
    'ORDER_UPDATED': 'Order updated successfully',
    'PAYMENT_SUCCESSFUL': 'Payment processed successfully',
    'COUPON_APPLIED': 'Coupon applied successfully',
    'LOGIN_SUCCESSFUL': 'Logged in successfully',
    'LOGOUT_SUCCESSFUL': 'Logged out successfully',
}
