from sqlalchemy import func
from database import db

class Setting(db.Model):
    __tablename__ = 'setting'

    id = db.Column(db.Integer, primary_key=True)
    store_name = db.Column(db.String(100), nullable=False)
    store_email = db.Column(db.String(120), unique=True, nullable=False)
    store_phone = db.Column(db.String(20), nullable=True)
    store_address = db.Column(db.Text, nullable=True)
    store_city = db.Column(db.String(50), nullable=True)
    store_country = db.Column(db.String(50), nullable=True)
    currency = db.Column(db.String(3), default='USD')
    language = db.Column(db.String(20), default='English')
    timezone = db.Column(db.String(50), default='UTC')
    logo_url = db.Column(db.String(255), nullable=True)
    tax_rate = db.Column(db.Float, default=0)
    shipping_cost = db.Column(db.Float, default=0)
    
    updated_at = db.Column(db.DateTime, onupdate=func.now(), server_default=func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'store_name': self.store_name,
            'store_email': self.store_email,
            'store_phone': self.store_phone,
            'store_address': self.store_address,
            'store_city': self.store_city,
            'store_country': self.store_country,
            'currency': self.currency,
            'language': self.language,
            'timezone': self.timezone,
            'logo_url': self.logo_url,
            'tax_rate': self.tax_rate,
            'shipping_cost': self.shipping_cost,
        }
