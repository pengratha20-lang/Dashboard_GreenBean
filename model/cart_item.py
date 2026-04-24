from sqlalchemy import UniqueConstraint, func

from core.database import db


class CartItem(db.Model):
    __tablename__ = 'cart_item'
    __table_args__ = (
        UniqueConstraint('customer_id', 'product_id', name='uq_cart_item_customer_product'),
    )

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

    customer = db.relationship('Customer', backref=db.backref('cart_items', lazy=True, cascade='all, delete-orphan'))
    product = db.relationship('Product', lazy='joined')

    def __repr__(self):
        return f'<CartItem customer={self.customer_id} product={self.product_id} qty={self.quantity}>'
