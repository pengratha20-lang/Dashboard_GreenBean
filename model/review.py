from sqlalchemy import func
from core.database import db

class Review(db.Model):
    __tablename__ = 'review'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)  # which order triggered review
    rating = db.Column(db.Integer, nullable=False)  # 1–5 stars
    title = db.Column(db.String(100), nullable=True)
    body = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'

    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())

    # Relationships
    product = db.relationship('Product', backref='reviews', lazy=True)
    customer = db.relationship('Customer', backref='reviews', lazy=True)
    order = db.relationship('Order', backref='reviews', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.product_name if self.product else '',
            'customer_id': self.customer_id,
            'customer_name': self.customer.name if self.customer else '',
            'order_id': self.order_id,
            'rating': self.rating,
            'title': self.title,
            'body': self.body,
            'status': self.status,
            'created_at': self.created_at.strftime('%b %d, %Y') if self.created_at else '',
        }
