from flask import Flask

from routes.main.frontside import checkout as checkout_module


class _FakeOrder:
    def __init__(self, **kwargs):
        self.id = None
        for key, value in kwargs.items():
            setattr(self, key, value)


class _FakeOrderItem:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class _FakeInvoice:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class _FakeSession:
    def __init__(self):
        self.added = []
        self.flushed = False
        self.committed = False

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        self.flushed = True
        for obj in self.added:
            if hasattr(obj, 'order_number') and getattr(obj, 'id', None) is None:
                obj.id = 101
                break

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


def test_validate_checkout_customer_info_success():
    data = checkout_module._validate_checkout_customer_info(
        'Alice Customer',
        'alice@example.com',
        '+85512345678',
        '123 Garden Road',
        'Phnom Penh',
        'Cambodia',
    )
    assert data['email'] == 'alice@example.com'
    assert data['name'] == 'Alice Customer'


def test_validate_checkout_customer_info_invalid_email():
    try:
        checkout_module._validate_checkout_customer_info(
            'Alice Customer',
            'alice-at-example.com',
            '+85512345678',
            '123 Garden Road',
            'Phnom Penh',
            'Cambodia',
        )
        assert False, 'Expected ValueError for invalid email'
    except ValueError as exc:
        assert 'Invalid email format' in str(exc)


def test_safe_api_error_payload():
    app = Flask(__name__)
    with app.app_context():
        response, status_code = checkout_module._safe_api_error('Bad request', 400)
        assert status_code == 400
        assert response.get_json() == {'success': False, 'message': 'Bad request'}


def test_create_order_with_invoice_reserve_stock(monkeypatch):
    import model.invoice as invoice_module

    fake_session = _FakeSession()
    fake_product = type('Product', (), {'product_name': 'Test Plant', 'stock': 5})()
    validated_items = [{
        'product': fake_product,
        'product_id': 1,
        'quantity': 2,
        'unit_price': 12.5,
    }]

    monkeypatch.setattr(checkout_module, 'Order', _FakeOrder)
    monkeypatch.setattr(checkout_module, 'OrderItem', _FakeOrderItem)
    monkeypatch.setattr(invoice_module, 'Invoice', _FakeInvoice)
    monkeypatch.setattr(checkout_module.db, 'session', fake_session, raising=False)

    order, invoice = checkout_module._create_order_with_invoice(
        cart_items=[{'id': 1, 'quantity': 2}],
        customer_id=1,
        currency='USD',
        payment_method='credit_card',
        coupon_code=None,
        order_summary={'subtotal': 25.0, 'shipping_cost': 0.0, 'discount': 0.0, 'total': 25.0},
        name='Alice Customer',
        email='alice@example.com',
        phone='+85512345678',
        address='123 Garden Road',
        city='Phnom Penh',
        country='Cambodia',
        reserve_stock=True,
        validated_items=validated_items,
    )

    assert order.id == 101
    assert invoice.order_id == 101
    assert fake_product.stock == 3
    assert fake_session.flushed is True
    assert fake_session.committed is True
