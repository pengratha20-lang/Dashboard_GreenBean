from model.product import Product
from model.category import Category
from model.customer import Customer
from model.user import User
from model.order import Order, OrderItem
from model.discount import Discount, DiscountProduct
from model.setting import Setting
from model.cart_item import CartItem
from model.wishlist import Wishlist
from model.stock_log import StockLog
from model.payment import Payment
from model.review import Review
from model.supplier import Supplier, Purchase, PurchaseItem

def init_models(db_instance):
    """Initialize all models (already defined in their modules)"""
    return Product, Category

__all__ = [
    'init_models',
    'Product', 'Category', 'Customer', 'User',
    'Order', 'OrderItem',
    'Discount', 'DiscountProduct',
    'Setting', 'CartItem', 'Wishlist',
    'StockLog', 'Payment', 'Review',
    'Supplier', 'Purchase', 'PurchaseItem',
]
