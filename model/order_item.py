# Order Item model
# OrderItem is defined in model/order.py alongside Order for relational clarity.
# This file re-exports OrderItem for STRUCTURE.md compliance.

from model.order import OrderItem

__all__ = ['OrderItem']
