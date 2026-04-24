from sqlalchemy import func, ForeignKey
from core.database import db
from datetime import datetime

class Invoice(db.Model):
    __tablename__ = 'invoice'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, ForeignKey('order.id'), nullable=False, unique=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    
    # Customer info snapshot (for historical records)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    customer_phone = db.Column(db.String(20))
    
    # Shipping info
    shipping_address = db.Column(db.Text, nullable=False)
    
    # Amount details
    subtotal = db.Column(db.Float, nullable=False)
    shipping_cost = db.Column(db.Float, default=0)
    discount_amount = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float, nullable=False)
    
    # Payment info
    payment_method = db.Column(db.String(50), nullable=False)  # 'credit_card', 'bakong'
    currency = db.Column(db.String(10), default='USD')
    
    # Status
    status = db.Column(db.String(20), default='issued')  # issued, paid, cancelled
    
    # Timestamps
    issued_at = db.Column(db.DateTime, server_default=func.now())
    due_at = db.Column(db.DateTime, nullable=True)
    paid_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())
    
    # Notes
    notes = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'order_id': self.order_id,
            'customer_name': self.customer_name,
            'customer_email': self.customer_email,
            'customer_phone': self.customer_phone,
            'shipping_address': self.shipping_address,
            'subtotal': self.subtotal,
            'shipping_cost': self.shipping_cost,
            'discount_amount': self.discount_amount,
            'total_amount': self.total_amount,
            'payment_method': self.payment_method,
            'currency': self.currency,
            'status': self.status,
            'issued_at': self.issued_at.strftime('%b %d, %Y %I:%M %p') if self.issued_at else '',
            'paid_at': self.paid_at.strftime('%b %d, %Y %I:%M %p') if self.paid_at else '',
        }
