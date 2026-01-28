from model.product import init_product_model
from model.category import init_category_model


def init_models(db):
    """Initialize all models"""
    Product = init_product_model(db)
    Category = init_category_model(db)
    return Product, Category


__all__ = ['init_models', 'init_product_model', 'init_category_model']