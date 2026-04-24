"""
Security and application logging utilities.
Provides centralized logging for security events, API calls, and errors.
"""

import logging
import json
import os
from datetime import datetime
from functools import wraps
from flask import request, g


class SecurityLogger:
    """Handles security-related logging"""
    
    def __init__(self, name='security'):
        self.logger = logging.getLogger(name)
        self._setup_handler()
    
    def _setup_handler(self):
        """Configure logging handler if not already configured"""
        if not self.logger.handlers:
            # Create logs directory if it doesn't exist
            os.makedirs('logs', exist_ok=True)
            handler = logging.FileHandler('logs/security.log')
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def log_authentication_attempt(self, username, success, ip_address=None):
        """Log authentication attempt"""
        status = "SUCCESS" if success else "FAILED"
        ip = ip_address or self._get_ip()
        self.logger.warning(f"Authentication {status}: user={username}, ip={ip}")
    
    def log_authorization_failure(self, user_id, action, resource, ip_address=None):
        """Log authorization failure"""
        ip = ip_address or self._get_ip()
        self.logger.warning(
            f"Authorization FAILED: user={user_id}, action={action}, "
            f"resource={resource}, ip={ip}"
        )
    
    def log_payment_attempt(self, order_id, method, amount, success, error=None):
        """Log payment attempt"""
        status = "SUCCESS" if success else "FAILED"
        msg = f"Payment {status}: order={order_id}, method={method}, amount={amount}"
        if error:
            msg += f", error={error}"
        self.logger.info(msg)
    
    def log_suspicious_activity(self, activity_type, user_id=None, details=None):
        """Log suspicious activity"""
        ip = self._get_ip()
        msg = f"SUSPICIOUS ACTIVITY: type={activity_type}, ip={ip}"
        if user_id:
            msg += f", user={user_id}"
        if details:
            msg += f", details={details}"
        self.logger.warning(msg)
    
    def log_password_change(self, user_id, success):
        """Log password change"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"Password change {status}: user={user_id}")
    
    def log_session_lifecycle(self, event, user_id=None, session_type=None):
        """
        Log session events (login, logout, timeout)
        
        Args:
            event: 'login', 'logout', 'timeout', 'extend'
            user_id: User ID (if applicable)
            session_type: 'admin' or 'customer'
        """
        ip = self._get_ip()
        msg = f"Session {event.upper()}: ip={ip}"
        if user_id:
            msg += f", user={user_id}"
        if session_type:
            msg += f", type={session_type}"
        self.logger.info(msg)
    
    def warning(self, message):
        """Generic warning logger for direct use"""
        self.logger.warning(message)
    
    def info(self, message):
        """Generic info logger for direct use"""
        self.logger.info(message)
    
    def error(self, message):
        """Generic error logger for direct use"""
        self.logger.error(message)
    
    @staticmethod
    def _get_ip():
        """Get client IP address"""
        if request:
            return request.environ.get('REMOTE_ADDR', 'unknown')
        return 'unknown'


class ApplicationLogger:
    """Handles general application logging"""
    
    def __init__(self, name='app'):
        self.logger = logging.getLogger(name)
        self._setup_handler()
    
    def _setup_handler(self):
        """Configure logging handler if not already configured"""
        if not self.logger.handlers:
            handler = logging.FileHandler('logs/application.log')
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def log_api_call(self, method, endpoint, status_code, user_id=None):
        """Log API call"""
        msg = f"API: {method} {endpoint} - Status: {status_code}"
        if user_id:
            msg += f" - User: {user_id}"
        self.logger.info(msg)
    
    def log_error(self, error_type, error_message, stack_trace=None):
        """Log application error"""
        msg = f"ERROR: {error_type} - {error_message}"
        if stack_trace:
            msg += f"\n{stack_trace}"
        self.logger.error(msg)
    
    def log_database_operation(self, operation, entity_type, entity_id=None, success=True):
        """Log database operations"""
        status = "SUCCESS" if success else "FAILED"
        msg = f"DB {status}: {operation} {entity_type}"
        if entity_id:
            msg += f" (ID: {entity_id})"
        self.logger.info(msg)
    
    def log_file_operation(self, operation, filename, success=True, error=None):
        """Log file operations"""
        status = "SUCCESS" if success else "FAILED"
        msg = f"FILE {status}: {operation} {filename}"
        if error:
            msg += f" - {error}"
        self.logger.info(msg)


# Global logger instances
security_logger = SecurityLogger('security')
app_logger = ApplicationLogger('app')


def log_api_endpoint(f):
    """Decorator to log API endpoint calls with request/response info"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = get_current_user_id()
        try:
            result = f(*args, **kwargs)
            app_logger.log_api_call(
                request.method,
                request.path,
                200,
                user_id
            )
            return result
        except Exception as e:
            app_logger.log_api_call(
                request.method,
                request.path,
                500,
                user_id
            )
            raise
    
    return decorated_function


def log_authentication(f):
    """Decorator to log authentication events"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        username = request.form.get('username') or request.json.get('username') if request.is_json else None
        try:
            result = f(*args, **kwargs)
            security_logger.log_authentication_attempt(username, True)
            return result
        except Exception as e:
            security_logger.log_authentication_attempt(username, False)
            raise
    
    return decorated_function


def get_current_user_id():
    """Get current user ID from session or request context"""
    from flask import session
    return session.get('admin_user_id') or session.get('customer_id') or None


def sanitize_error_message(error):
    """
    Convert internal error to user-friendly message.
    Logs full error server-side and returns sanitized message to client.
    
    Args:
        error: Exception object
        
    Returns:
        tuple: (user_message, status_code)
    """
    from core.exceptions import ApplicationError
    
    # Log full error
    app_logger.log_error(
        type(error).__name__,
        str(error),
        getattr(error, '__traceback__', None)
    )
    
    # Return appropriate user message
    if isinstance(error, ApplicationError):
        return error.message, error.status_code
    
    # Generic error message for unexpected exceptions
    return "An error occurred. Please try again later.", 500
