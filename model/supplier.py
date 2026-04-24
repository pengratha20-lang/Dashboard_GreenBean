from sqlalchemy import func
from core.database import db

class Supplier(db.Model):
    __tablename__ = 'supplier'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(50), nullable=True)
    country = db.Column(db.String(50), nullable=True)
    contact_person = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='active')  # 'active', 'inactive'

    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())

    # Relationship to purchases
    purchases = db.relationship('Purchase', backref='supplier', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'country': self.country,
            'contact_person': self.contact_person,
            'status': self.status,
            'created_at': self.created_at.strftime('%b %d, %Y') if self.created_at else '',
        }


class Purchase(db.Model):
    """Records stock purchases from suppliers"""
    __tablename__ = 'purchase'

    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # admin who recorded it
    total_amount = db.Column(db.Float, nullable=False, default=0)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'received', 'cancelled'
    note = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())

    # Relationship
    user = db.relationship('User', backref='purchases', lazy=True)
    items = db.relationship('PurchaseItem', backref='purchase', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier.name if self.supplier else '',
            'total_amount': self.total_amount,
            'status': self.status,
            'note': self.note,
            'item_count': len(self.items),
            'created_at': self.created_at.strftime('%b %d, %Y') if self.created_at else '',
        }


class PurchaseItem(db.Model):
    """Line items for a purchase order"""
    __tablename__ = 'purchase_item'

    id = db.Column(db.Integer, primary_key=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchase.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_cost = db.Column(db.Float, nullable=False)

    created_at = db.Column(db.DateTime, server_default=func.now())

    # Relationship
    product = db.relationship('Product', backref='purchase_items', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'purchase_id': self.purchase_id,
            'product_id': self.product_id,
            'product_name': self.product.product_name if self.product else '',
            'quantity': self.quantity,
            'unit_cost': self.unit_cost,
            'subtotal': self.quantity * self.unit_cost,
        }
