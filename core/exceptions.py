"""
Custom exception classes for the application.
Provides structured error handling for different error scenarios.
"""


class ApplicationError(Exception):
    """Base application exception"""
    def __init__(self, message, status_code=400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


# Payment-related exceptions
class PaymentError(ApplicationError):
    """Base payment exception"""
    def __init__(self, message, status_code=400):
        super().__init__(message, status_code)


class InvalidPaymentMethod(PaymentError):
    """Invalid payment method selected"""
    def __init__(self):
        super().__init__("Invalid payment method selected", 400)


class InvalidCurrency(PaymentError):
    """Unsupported currency"""
    def __init__(self, currency=None):
        msg = f"Unsupported currency: {currency}" if currency else "Unsupported currency"
        super().__init__(msg, 400)


class KHQRError(PaymentError):
    """KHQR-specific payment errors"""
    def __init__(self, message):
        super().__init__(f"KHQR Error: {message}", 400)


class InvalidKHQRConfig(KHQRError):
    """Missing or invalid KHQR configuration"""
    def __init__(self):
        super().__init__("Missing or invalid KHQR configuration")


# Authentication-related exceptions
class AuthenticationError(ApplicationError):
    """Authentication failed"""
    def __init__(self, message="Authentication failed"):
        super().__init__(message, 401)


class InvalidCredentials(AuthenticationError):
    """Invalid username or password"""
    def __init__(self):
        super().__init__("Invalid username or password")


class UnauthorizedAccess(ApplicationError):
    """User not authorized for this action"""
    def __init__(self, message="Unauthorized access"):
        super().__init__(message, 403)


class AdminRequired(UnauthorizedAccess):
    """Admin privileges required"""
    def __init__(self):
        super().__init__("Admin privileges required")


# Validation exceptions
class ValidationError(ApplicationError):
    """Input validation failed"""
    def __init__(self, message, field=None):
        self.field = field
        super().__init__(message, 400)


class InvalidAmount(ValidationError):
    """Invalid monetary amount"""
    def __init__(self):
        super().__init__("Amount must be greater than zero", "amount")


class InvalidEmail(ValidationError):
    """Invalid email address"""
    def __init__(self):
        super().__init__("Invalid email address", "email")


class InvalidPhone(ValidationError):
    """Invalid phone number"""
    def __init__(self):
        super().__init__("Invalid phone number", "phone")


# Database-related exceptions
class DatabaseError(ApplicationError):
    """Database operation failed"""
    def __init__(self, message="Database operation failed"):
        super().__init__(message, 500)


class EntityNotFound(ApplicationError):
    """Requested entity not found"""
    def __init__(self, entity_type, entity_id=None):
        msg = f"{entity_type} not found"
        if entity_id:
            msg += f" (ID: {entity_id})"
        super().__init__(msg, 404)


class DuplicateEntry(ApplicationError):
    """Duplicate entry in database"""
    def __init__(self, field, value):
        super().__init__(f"A record with {field}='{value}' already exists", 409)


# File operation exceptions
class FileOperationError(ApplicationError):
    """File operation failed"""
    def __init__(self, message="File operation failed"):
        super().__init__(message, 400)


class InvalidFileType(FileOperationError):
    """Invalid file type"""
    def __init__(self, allowed_types=None):
        msg = "Invalid file type"
        if allowed_types:
            msg += f". Allowed types: {', '.join(allowed_types)}"
        super().__init__(msg)


class FileTooLarge(FileOperationError):
    """File size exceeds limit"""
    def __init__(self, max_size):
        super().__init__(f"File size exceeds maximum limit of {max_size}MB")


# Coupon/Discount exceptions
class CouponError(ApplicationError):
    """Coupon operation failed"""
    def __init__(self, message):
        super().__init__(message, 400)


class InvalidCoupon(CouponError):
    """Coupon is invalid or expired"""
    def __init__(self):
        super().__init__("Invalid or expired coupon code")


class CouponLimitExceeded(CouponError):
    """Coupon usage limit exceeded"""
    def __init__(self):
        super().__init__("Coupon usage limit has been exceeded")


# Order-related exceptions
class OrderError(ApplicationError):
    """Order operation failed"""
    def __init__(self, message):
        super().__init__(message, 400)


class InvalidOrderStatus(OrderError):
    """Invalid order status transition"""
    def __init__(self, current_status, requested_status):
        super().__init__(
            f"Cannot transition order from {current_status} to {requested_status}"
        )


class InsufficientStock(OrderError):
    """Product stock insufficient"""
    def __init__(self, product_name, available, requested):
        super().__init__(
            f"Insufficient stock for {product_name}. Available: {available}, Requested: {requested}"
        )
