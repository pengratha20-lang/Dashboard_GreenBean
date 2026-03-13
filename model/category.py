from email.policy import default


def init_category_model(db):
    """Initialize Category model"""
    
    class Category(db.Model):
        __tablename__ = 'category'
        __table_args__ = {'extend_existing': True}
        
        id = db.Column(db.Integer, primary_key=True)
        category_name = db.Column(db.String(80), unique=True, nullable=False)
        description = db.Column(db.String(500), nullable=True)
        icon = db.Column(db.String(80), default='fa-leaf')

        def __repr__(self):
            return f'<Category {self.category_name}>'
    
    return Category
