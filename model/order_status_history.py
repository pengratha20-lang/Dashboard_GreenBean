"""
Order Status History - Track all status changes for orders
"""
from sqlalchemy import func
from core.database import db
from datetime import datetime

class OrderStatusHistory(db.Model):
    __tablename__ = 'order_status_history'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    old_status = db.Column(db.String(20), nullable=True)  # Previous status (null if first entry)
    new_status = db.Column(db.String(20), nullable=False)  # Current status
    changed_by = db.Column(db.String(100), default='system')  # User or 'system'
    notes = db.Column(db.Text, nullable=True)  # Reason for change
    created_at = db.Column(db.DateTime, server_default=func.now())
    
    # Relationships
    order = db.relationship('Order', backref='status_history', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'old_status': self.old_status,
            'new_status': self.new_status,
            'changed_by': self.changed_by,
            'notes': self.notes,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else ''
        }
    
    @staticmethod
    def create_entry(order_id, new_status, old_status=None, changed_by='system', notes=None):
        """Create a new status history entry"""
        entry = OrderStatusHistory(
            order_id=order_id,
            old_status=old_status,
            new_status=new_status,
            changed_by=changed_by,
            notes=notes
        )
        db.session.add(entry)
        return entry
