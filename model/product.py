from datetime import datetime
from sqlalchemy import func


def init_product_model(db):

    class Product(db.Model):
        __tablename__ = 'product'
        
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
    
    return Product
