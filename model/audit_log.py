"""
Audit log model for tracking all administrative actions and sensitive operations.
Essential for compliance, security monitoring, and forensic analysis.
"""

from core.database import db
from datetime import datetime


class AuditLog(db.Model):
    """
    Record of all administrative and sensitive operations.
    Used for security monitoring, compliance, and forensic analysis.
    """
    __tablename__ = 'audit_log'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Who performed the action
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True, index=True)
    
    # What action was performed
    action = db.Column(db.String(100), nullable=False, index=True)
    
    # What entity was affected
    entity_type = db.Column(db.String(50), nullable=False, index=True)  # e.g., 'product', 'order', 'user'
    entity_id = db.Column(db.Integer, nullable=True, index=True)
    
    # Additional context
    description = db.Column(db.Text, nullable=True)
    
    # Before/after values for updates (stored as JSON strings for comparison)
    old_values = db.Column(db.Text, nullable=True)  # JSON
    new_values = db.Column(db.Text, nullable=True)  # JSON
    
    # System info
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 support
    user_agent = db.Column(db.String(255), nullable=True)
    
    # Status
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<AuditLog {self.id}: {self.action} on {self.entity_type}({self.entity_id}) by user {self.admin_id or self.customer_id}>'
    
    def to_dict(self):
        """Convert audit log to dictionary"""
        return {
            'id': self.id,
            'admin_id': self.admin_id,
            'customer_id': self.customer_id,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'description': self.description,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'ip_address': self.ip_address,
            'success': self.success,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class LoginAttempt(db.Model):
    """
    Track login attempts for security monitoring and brute force protection.
    """
    __tablename__ = 'login_attempt'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Login info
    username = db.Column(db.String(255), nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=False, index=True)
    
    # Result
    success = db.Column(db.Boolean, default=False, index=True)
    failure_reason = db.Column(db.String(255), nullable=True)  # e.g., 'invalid_password', 'user_not_found'
    
    # User info
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user_type = db.Column(db.String(20), nullable=False)  # 'admin' or 'customer'
    
    # Timestamp
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        status = 'SUCCESS' if self.success else 'FAILED'
        return f'<LoginAttempt {status}: {self.username} from {self.ip_address} at {self.attempted_at}>'
    
    def to_dict(self):
        """Convert login attempt to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'ip_address': self.ip_address,
            'success': self.success,
            'failure_reason': self.failure_reason,
            'user_id': self.user_id,
            'user_type': self.user_type,
            'attempted_at': self.attempted_at.isoformat() if self.attempted_at else None,
        }


class DataExportLog(db.Model):
    """
    Track data exports for compliance and audit purposes.
    """
    __tablename__ = 'data_export_log'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Who exported
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    
    # What was exported
    export_type = db.Column(db.String(100), nullable=False)  # e.g., 'orders', 'customers', 'products'
    export_format = db.Column(db.String(20), nullable=False)  # 'csv', 'json', 'excel'
    
    # Filter criteria (for audit trail)
    filter_criteria = db.Column(db.Text, nullable=True)  # JSON
    
    # Result
    record_count = db.Column(db.Integer, nullable=False)
    file_path = db.Column(db.String(255), nullable=True)
    file_size_bytes = db.Column(db.Integer, nullable=True)
    
    # Access info
    ip_address = db.Column(db.String(45), nullable=True)
    
    # Timestamp
    exported_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<DataExportLog: {self.export_type}({self.record_count} records) exported by user {self.admin_id}>'
    
    def to_dict(self):
        """Convert export log to dictionary"""
        return {
            'id': self.id,
            'admin_id': self.admin_id,
            'export_type': self.export_type,
            'export_format': self.export_format,
            'record_count': self.record_count,
            'file_size_bytes': self.file_size_bytes,
            'exported_at': self.exported_at.isoformat() if self.exported_at else None,
        }


class SecurityEvent(db.Model):
    """
    Track security events like failed validations, unauthorized access attempts, etc.
    """
    __tablename__ = 'security_event'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Event classification
    event_type = db.Column(db.String(100), nullable=False, index=True)  # e.g., 'invalid_payment', 'csrf_failed', 'auth_bypass_attempt'
    severity = db.Column(db.String(20), nullable=False)  # 'low', 'medium', 'high', 'critical'
    
    # Who/What
    user_id = db.Column(db.Integer, nullable=True, index=True)
    ip_address = db.Column(db.String(45), nullable=False, index=True)
    
    # Details
    description = db.Column(db.Text, nullable=False)
    additional_data = db.Column(db.Text, nullable=True)  # JSON for extra context
    
    # Response taken
    action_taken = db.Column(db.String(255), nullable=True)  # e.g., 'blocked', 'flagged', 'logged'
    
    # Timestamp
    occurred_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<SecurityEvent {self.event_type}[{self.severity}]: {self.description}>'
    
    def to_dict(self):
        """Convert security event to dictionary"""
        return {
            'id': self.id,
            'event_type': self.event_type,
            'severity': self.severity,
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'description': self.description,
            'action_taken': self.action_taken,
            'occurred_at': self.occurred_at.isoformat() if self.occurred_at else None,
        }
