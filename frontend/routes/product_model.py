"""Product model for SQLAlchemy ORM"""
from sqlalchemy import func
from database import db


class Product(db.Model):
    __tablename__ = 'product'

    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    image = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='active')
    category_id = db.Column(db.Integer, nullable=True)
    
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())
    
    # Relationship to Discounts (many-to-many)
    discounts = db.relationship('Discount', secondary='discount_product', backref=db.backref('products', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.product_name,
            'price': self.price,
            'stock': self.stock,
            'image': self.image,
            'description': self.description,
            'status': self.status,
        }
