from sqlalchemy import func
from core.database import db

class Payment(db.Model):
    __tablename__ = 'payment'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # 'cash', 'card', 'transfer', 'gopay', 'ovo', etc.
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'paid', 'failed', 'refunded'
    transaction_id = db.Column(db.String(100), nullable=True, unique=True)  # external payment ref
    paid_at = db.Column(db.DateTime, nullable=True)
    note = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())

    # Relationship
    order = db.relationship('Order', backref='payments', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'order_number': self.order.order_number if self.order else '',
            'payment_method': self.payment_method,
            'amount': self.amount,
            'status': self.status,
            'transaction_id': self.transaction_id,
            'paid_at': self.paid_at.strftime('%b %d, %Y %H:%M') if self.paid_at else None,
            'note': self.note,
            'created_at': self.created_at.strftime('%b %d, %Y') if self.created_at else '',
        }
