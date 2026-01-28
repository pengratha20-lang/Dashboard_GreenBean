"""
Database module - Initialize SQLAlchemy without circular imports
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
