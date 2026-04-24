from sqlalchemy import func
from core.database import db

class StockLog(db.Model):
    __tablename__ = 'stock_log'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # admin who made the change
    change_type = db.Column(db.String(20), nullable=False)  # 'restock', 'sale', 'adjustment', 'return', 'initial'
    quantity_before = db.Column(db.Integer, nullable=False)
    quantity_change = db.Column(db.Integer, nullable=False)  # positive = add, negative = remove
    quantity_after = db.Column(db.Integer, nullable=False)
    note = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, server_default=func.now())

    # Relationships
    product = db.relationship('Product', backref='stock_logs', lazy=True)
    user = db.relationship('User', backref='stock_logs', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.product_name if self.product else '',
            'user_id': self.user_id,
            'changed_by': self.user.username if self.user else 'System',
            'change_type': self.change_type,
            'quantity_before': self.quantity_before,
            'quantity_change': self.quantity_change,
            'quantity_after': self.quantity_after,
            'note': self.note,
            'created_at': self.created_at.strftime('%b %d, %Y %H:%M') if self.created_at else '',
        }
    
    @staticmethod
    def create_entry(product_id, change_type, quantity_before, quantity_change, quantity_after, note=None, user_id=None):
        """Create a new stock log entry"""
        entry = StockLog(
            product_id=product_id,
            user_id=user_id,
            change_type=change_type,
            quantity_before=quantity_before,
            quantity_change=quantity_change,
            quantity_after=quantity_after,
            note=note
        )
        db.session.add(entry)
        return entry
