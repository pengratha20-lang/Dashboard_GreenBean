from app import app
from core.database import db
from model.category import Category
from model.order import Order
from model.product import Product
from uuid import uuid4


def _create_test_product():
    category = Category.query.first()
    if not category:
        category = Category(category_name='Integration Test Category', icon='fa-leaf')
        db.session.add(category)
        db.session.commit()

    product = Product(
        product_name=f'Integration Test Product {uuid4().hex[:8]}',
        price=14.0,
        stock=8,
        category_id=category.id,
        status='active',
        description='Integration test product',
    )
    db.session.add(product)
    db.session.commit()

    return product


def test_checkout_route_sequence_with_minimal_sync_payload():
    with app.app_context():
        product = _create_test_product()
        product_id = product.id
        initial_stock = product.stock
        initial_order_count = Order.query.count()

    with app.test_client() as client:
        sync_response = client.post('/sync-cart', json={
            'cart_items': [{'id': product_id, 'quantity': 2}],
            'coupon_code': None,
        })
        assert sync_response.status_code == 200
        sync_body = sync_response.get_json()
        assert sync_body['success'] is True
        assert sync_body['cart_count'] == 2

        checkout_response = client.get('/checkout')
        assert checkout_response.status_code == 200

        process_response = client.post('/checkout/process', data={
            'name': 'Integration User',
            'email': 'integration.user@example.com',
            'phone': '+85512345672',
            'address': '101 Integration Street',
            'city': 'Phnom Penh',
            'country': 'Cambodia',
            'payment_method': 'credit_card',
            'currency': 'USD',
        }, follow_redirects=False)
        assert process_response.status_code == 302
        location = process_response.headers.get('Location', '')
        assert '/order-confirmation/' in location

        confirmation_response = client.get(location)
        assert confirmation_response.status_code == 200

    with app.app_context():
        updated_product = Product.query.get(product_id)
        assert updated_product is not None
        assert updated_product.stock == initial_stock - 2
        assert Order.query.count() == initial_order_count + 1
