from sqlalchemy import func
from core.database import db

class Wishlist(db.Model):
    __tablename__ = 'wishlist'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    product_price = db.Column(db.Float, nullable=False)
    product_image = db.Column(db.String(255), nullable=True)
    
    created_at = db.Column(db.DateTime, server_default=func.now())
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'product_price': self.product_price,
            'product_image': self.product_image,
            'created_at': self.created_at.strftime('%b %d, %Y') if self.created_at else '',
        }
