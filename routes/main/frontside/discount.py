from sqlalchemy import func
from database import db

class Discount(db.Model):
    __tablename__ = 'discount'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    discount_type = db.Column(db.String(20), default='percentage')  # 'percentage' or 'fixed'
    discount_value = db.Column(db.Float, nullable=False)
    min_purchase = db.Column(db.Float, default=0)
    # Global usage limit across all customers (None = unlimited)
    max_usage = db.Column(db.Integer, nullable=True)
    usage_count = db.Column(db.Integer, default=0)
    # Per-customer usage limit (e.g. 1 or 2 times per customer, None = unlimited)
    max_usage_per_customer = db.Column(db.Integer, nullable=True)
    expiry_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='active')  # 'active' or 'inactive'
    
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())
    
    # Relationship to Products (many-to-many through discount_product) - will be set up after Product is defined
    # products = db.relationship('Product', secondary='discount_product', backref=db.backref('discounts', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'description': self.description,
            'discount_type': self.discount_type,
            'discount_value': self.discount_value,
            'min_purchase': self.min_purchase,
            'max_usage': self.max_usage,
            'usage_count': self.usage_count,
            'max_usage_per_customer': self.max_usage_per_customer,
            'expiry_date': self.expiry_date.strftime('%b %d, %Y') if self.expiry_date else '',
            'status': self.status,
        }

class DiscountProduct(db.Model):
    __tablename__ = 'discount_product'
    
    id = db.Column(db.Integer, primary_key=True)
    discount_id = db.Column(db.Integer, db.ForeignKey('discount.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)  # Don't enforce FK to product table since it's in SQLite
    
    created_at = db.Column(db.DateTime, server_default=func.now())
