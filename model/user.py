from sqlalchemy import func
from database import db

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    profile_pic = db.Column(db.String(80), nullable=False)

    created_at = db.Column(db.DateTime, server_default=func.now())
