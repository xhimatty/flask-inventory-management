import os
import pytest
from app import app
from app.extensions import db
from app.models import User, Products, Category


os.environ['DATABASE'] = 'sqlite://'


@pytest.fixture
def test_app():
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['PROPAGATE_EXCEPTIONS'] = False
    
    with app.app_context():
        db.create_all()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(test_app):
    return test_app.test_client()


@pytest.fixture
def employee_client(client):
    user = User(
        name='Test Employee',
        username='testemployee',
        email='employee@test.com',
        role='employee'
    )
    user.set_password('testpassword')

    db.session.add(user)
    db.session.commit()

    client.post('/login', data={
        'username': 'testemployee',
        'password': 'testpassword'
    })

    return client


@pytest.fixture
def admin_client(client):
    user = User(
        name='Test Admin',
        username='testadmin',
        email='admin@test.com',
        role='admin'
    )
    user.set_password('testpassword')

    db.session.add(user)
    db.session.commit()

    client.post('/login', data={
        'username': 'testadmin',
        'password': 'testpassword'
    })

    return client


@pytest.fixture
def category():
    category = Category(name='Test Category')

    db.session.add(category)
    db.session.commit()

    return category


@pytest.fixture
def product(category):
    product = Products(
        name='Test Product',
        sku='TEST-001',
        price=10.00,
        qty=10,
        unit='pcs',
        reorder_level=5,
        description='Test description',
        category_id=category.id
    )

    db.session.add(product)
    db.session.commit()

    return product