"""
Input validation utilities for API endpoints.
Centralizes validation logic to prevent injection attacks and invalid data.
"""

import re
from decimal import Decimal, InvalidOperation
from core.exceptions import (
    ValidationError,
    InvalidEmail,
    InvalidPhone,
    InvalidAmount,
    InvalidPaymentMethod,
    InvalidCurrency,
    InvalidFileType,
)


# Regex patterns for validation
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
PHONE_PATTERN = re.compile(r'^\+?[\d\s\-\(\)]{7,20}$')
USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,32}$')
CURRENCY_PATTERN = re.compile(r'^[A-Z]{3}$')


def validate_email(email):
    """
    Validate email address format.
    
    Args:
        email (str): Email address to validate
        
    Returns:
        str: Validated email (lowercase)
        
    Raises:
        InvalidEmail: If email format is invalid
    """
    if not email or not isinstance(email, str):
        raise InvalidEmail()
    
    email = email.strip().lower()
    if not EMAIL_PATTERN.match(email):
        raise InvalidEmail()
    
    return email


def validate_phone(phone):
    """
    Validate phone number format.
    
    Args:
        phone (str): Phone number to validate
        
    Returns:
        str: Validated phone number
        
    Raises:
        InvalidPhone: If phone format is invalid
    """
    if not phone or not isinstance(phone, str):
        raise InvalidPhone()
    
    phone = phone.strip()
    if not PHONE_PATTERN.match(phone):
        raise InvalidPhone()
    
    return phone


def validate_username(username):
    """
    Validate username format (alphanumeric, dash, underscore only).
    
    Args:
        username (str): Username to validate
        
    Returns:
        str: Validated username
        
    Raises:
        ValidationError: If username format is invalid
    """
    if not username or not isinstance(username, str):
        raise ValidationError("Username is required", "username")
    
    username = username.strip()
    if not USERNAME_PATTERN.match(username):
        raise ValidationError(
            "Username must be 3-32 characters (letters, numbers, dash, underscore)",
            "username"
        )
    
    return username


def validate_password(password):
    """
    Validate password strength.
    
    Args:
        password (str): Password to validate
        
    Returns:
        str: Validated password
        
    Raises:
        ValidationError: If password is too weak
    """
    if not password or not isinstance(password, str):
        raise ValidationError("Password is required", "password")
    
    if len(password) < 6:
        raise ValidationError("Password must be at least 6 characters", "password")
    
    return password


def validate_amount(amount, min_value=0, max_value=999999):
    """
    Validate monetary amount.
    
    Args:
        amount: Amount to validate (int, float, str, or Decimal)
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        
    Returns:
        Decimal: Validated amount
        
    Raises:
        InvalidAmount: If amount is invalid
    """
    try:
        amount_decimal = Decimal(str(amount))
    except (InvalidOperation, ValueError, TypeError):
        raise InvalidAmount()
    
    if amount_decimal < Decimal(str(min_value)) or amount_decimal > Decimal(str(max_value)):
        raise ValidationError(
            f"Amount must be between {min_value} and {max_value}",
            "amount"
        )
    
    if amount_decimal <= 0:
        raise InvalidAmount()
    
    return amount_decimal


def validate_payment_method(method, allowed_methods=None):
    """
    Validate payment method against whitelist.
    
    Args:
        method (str): Payment method to validate
        allowed_methods (list): List of allowed methods. Defaults to ['credit_card', 'bakong']
        
    Returns:
        str: Validated payment method (lowercase)
        
    Raises:
        InvalidPaymentMethod: If method is not allowed
    """
    if allowed_methods is None:
        allowed_methods = ['credit_card', 'bakong']
    
    if not method or not isinstance(method, str):
        raise InvalidPaymentMethod()
    
    method = method.strip().lower()
    if method not in allowed_methods:
        raise InvalidPaymentMethod()
    
    return method


def validate_currency(currency, allowed_currencies=None):
    """
    Validate currency code against whitelist.
    
    Args:
        currency (str): Currency code to validate (e.g., 'USD', 'KHR')
        allowed_currencies (list): List of allowed currencies. Defaults to ['USD', 'KHR']
        
    Returns:
        str: Validated currency (uppercase)
        
    Raises:
        InvalidCurrency: If currency is not allowed
    """
    if allowed_currencies is None:
        allowed_currencies = ['USD', 'KHR']
    
    if not currency or not isinstance(currency, str):
        raise InvalidCurrency()
    
    currency = currency.strip().upper()
    if currency not in allowed_currencies:
        raise InvalidCurrency(currency)
    
    return currency


def validate_file_type(filename, allowed_extensions=None):
    """
    Validate file type by extension.
    
    Args:
        filename (str): Filename to validate
        allowed_extensions (list): Allowed file extensions (without dot). Defaults to image types
        
    Returns:
        str: File extension (lowercase)
        
    Raises:
        InvalidFileType: If file type is not allowed
    """
    if allowed_extensions is None:
        allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
    
    if not filename or '.' not in filename:
        raise InvalidFileType(allowed_extensions)
    
    ext = filename.rsplit('.', 1)[-1].lower()
    if ext not in allowed_extensions:
        raise InvalidFileType(allowed_extensions)
    
    return ext


def validate_string(value, field_name, min_length=1, max_length=255, allow_empty=False):
    """
    Validate string input.
    
    Args:
        value: Value to validate
        field_name (str): Name of field for error messages
        min_length: Minimum string length
        max_length: Maximum string length
        allow_empty: Whether to allow empty strings
        
    Returns:
        str: Validated and stripped string
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string", field_name)
    
    value = value.strip()
    
    if not value and not allow_empty:
        raise ValidationError(f"{field_name} is required", field_name)
    
    if len(value) < min_length:
        raise ValidationError(
            f"{field_name} must be at least {min_length} characters",
            field_name
        )
    
    if len(value) > max_length:
        raise ValidationError(
            f"{field_name} must not exceed {max_length} characters",
            field_name
        )
    
    return value


def validate_integer(value, field_name, min_value=None, max_value=None):
    """
    Validate integer input.
    
    Args:
        value: Value to validate
        field_name (str): Name of field for error messages
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        
    Returns:
        int: Validated integer
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        value = int(value)
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} must be an integer", field_name)
    
    if min_value is not None and value < min_value:
        raise ValidationError(
            f"{field_name} must be at least {min_value}",
            field_name
        )
    
    if max_value is not None and value > max_value:
        raise ValidationError(
            f"{field_name} must not exceed {max_value}",
            field_name
        )
    
    return value


def validate_url(url):
    """
    Validate URL format.
    
    Args:
        url (str): URL to validate
        
    Returns:
        str: Validated URL
        
    Raises:
        ValidationError: If URL format is invalid
    """
    if not url or not isinstance(url, str):
        raise ValidationError("URL is required", "url")
    
    url = url.strip()
    if not (url.startswith('http://') or url.startswith('https://')):
        raise ValidationError("URL must start with http:// or https://", "url")
    
    return url
