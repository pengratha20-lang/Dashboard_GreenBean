from core.database import db

class Category(db.Model):
    __tablename__ = 'category'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(500), nullable=True)
    icon = db.Column(db.String(80), default='fa-leaf')

    def __repr__(self):
        return f'<Category {self.category_name}>'

def init_category_model(db_instance):
    return Category
