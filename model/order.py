from sqlalchemy import func
from core.database import db

class Order(db.Model):
    __tablename__ = 'order'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)  # ✅ Changed to nullable=True for guest orders
    customer_name = db.Column(db.String(100), nullable=True)  # ✅ NEW: Store customer name for guest orders
    total_amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')  # USD or KHR - currency used for this order
    payment_method = db.Column(db.String(50), default='credit_card')  # credit_card or bakong
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, cancelled, payment_failed
    # Coupon / discount fields for Option B
    discount_id = db.Column(db.Integer, db.ForeignKey('discount.id'), nullable=True)
    coupon_code = db.Column(db.String(50), nullable=True)
    discount_amount = db.Column(db.Float, nullable=False, default=0)
    shipping_address = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())
    
    # Relationships
    customer = db.relationship('Customer', backref='orders', lazy=True)
    discount = db.relationship('Discount', backref='orders', lazy=True)
    order_items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        customer_name = self.customer.name if self.customer else 'Guest checkout'
        return {
            'id': self.id,
            'order_number': self.order_number,
            'customer_id': self.customer_id,
            'customer_name': customer_name,
            'total_amount': self.total_amount,
            'currency': self.currency,
            'payment_method': self.payment_method,
            'status': self.status,
            'discount_id': self.discount_id,
            'coupon_code': self.coupon_code,
            'discount_amount': self.discount_amount,
            'shipping_address': self.shipping_address,
            'notes': self.notes,
            'item_count': len(self.order_items),
            'created_at': self.created_at.strftime('%b %d, %Y') if self.created_at else '',
        }

class OrderItem(db.Model):
    __tablename__ = 'order_item'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    
    created_at = db.Column(db.DateTime, server_default=func.now())
    
    # Relationships
    product = db.relationship('Product', backref='order_items', lazy=True)
