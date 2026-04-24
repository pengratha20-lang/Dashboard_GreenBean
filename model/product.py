from sqlalchemy import func
from core.database import db
from core.image_helper import ImagePathHelper

class Product(db.Model):
    __tablename__ = 'product'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(80), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    image = db.Column(db.String(120), nullable=True)
    description = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='instock')
    create_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    update_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

    # Relationship to Category
    category = db.relationship('Category', backref='products', lazy=True)

    def __repr__(self):
        return f'<Product {self.product_name}>'
    
    # Image URL Helper Methods
    def get_thumbnail_image_url(self):
        """Get small thumbnail image URL (200x200) for dashboard/list view"""
        if self.image:
            return ImagePathHelper.get_url_path('product', self.image, 'thumbnail')
        return '/static/images/default-product-thumbnail.png'
    
    def get_card_image_url(self):
        """Get medium card image URL (400x400) for card display"""
        if self.image:
            return ImagePathHelper.get_url_path('product', self.image, 'resized')
        return '/static/images/default-product-card.png'
    
    def get_detail_image_url(self):
        """Get original full-size image URL for detail/modal view"""
        if self.image:
            return ImagePathHelper.get_url_path('product', self.image, 'original')
        return '/static/images/default-product-original.png'
    
    def get_all_image_urls(self):
        """Get all image versions as a dictionary"""
        return {
            'thumbnail': self.get_thumbnail_image_url(),
            'card': self.get_card_image_url(),
            'detail': self.get_detail_image_url()
        }

def init_product_model(db_instance):
    # This remains for backward compatibility in init_models if needed, 
    # but the class is now available at module level.
    return Product
