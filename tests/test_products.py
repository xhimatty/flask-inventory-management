from app.models import Products, Category
from app.extensions import db


def test_add_product(admin_client, category):
    response = admin_client.post('/products/add', data={
        'name': 'Test ESP32 Board',
        'sku': 'TEST-ESP32',
        'category_id': category.id,
        'price': '15.50',
        'qty': '10',
        'unit': 'pcs',
        'reorder_level': '5',
        'description': 'Test product'
    }, follow_redirects=True)

    assert response.status_code == 200

    product = db.session.scalar(
        db.select(Products).filter_by(sku='TEST-ESP32')
    )

    assert product is not None
    assert product.qty == 10


def test_view_product(admin_client, product):
    response = admin_client.get(f'/products/{product.id}')

    assert response.status_code == 200
    assert product.name.encode() in response.data


def test_edit_product(admin_client, product, category):
    response = admin_client.post(
        f'/products/{product.id}/edit',
        data={
            'name': 'Updated Product',
            'sku': product.sku,
            'category_id': category.id,
            'price': '25.00',
            'unit': 'pcs',
            'reorder_level': '5',
            'description': 'Updated description'
        },
        follow_redirects=True
    )

    assert response.status_code == 200

    db.session.refresh(product)

    assert product.name == 'Updated Product'
    assert float(product.price) == 25.00


def test_search_products(admin_client, product):
    response = admin_client.get(
        f'/products?search={product.name}'
    )

    assert response.status_code == 200
    assert product.name.encode() in response.data


def test_filter_out_of_stock(admin_client, category):
    item = Products(
        name='Empty Stock Product',
        sku='EMPTY-001',
        price=10,
        qty=0,
        unit='pcs',
        reorder_level=5,
        description='Test',
        category_id=category.id
    )

    db.session.add(item)
    db.session.commit()

    response = admin_client.get('/products?status=out_of_stock')

    assert response.status_code == 200
    assert b'Empty Stock Product' in response.data


def test_filter_by_category(admin_client, product, category):
    response = admin_client.get(
        f'/products?category={category.id}'
    )

    assert response.status_code == 200
    assert product.name.encode() in response.data


def test_product_pagination(admin_client, category):
    for number in range(12):
        product = Products(
            name=f'Pagination Product {number}',
            sku=f'PAGE-{number:03}',
            price=10,
            qty=10,
            unit='pcs',
            reorder_level=5,
            description='Pagination test',
            category_id=category.id
        )
        db.session.add(product)

    db.session.commit()

    response = admin_client.get('/products?page=2')

    assert response.status_code == 200


def test_deactivate_product(admin_client, product):
    response = admin_client.post(
        f'/products/{product.id}/status',
        data={'action': 'deactivate'},
        follow_redirects=True
    )

    assert response.status_code == 200

    db.session.refresh(product)

    assert product.is_active is False


def test_activate_product(admin_client, product):
    product.is_active = False
    db.session.commit()

    response = admin_client.post(
        f'/products/{product.id}/status',
        data={'action': 'activate'},
        follow_redirects=True
    )

    assert response.status_code == 200

    db.session.refresh(product)

    assert product.is_active is True


def test_soft_delete_product(admin_client, product):
    product.qty = 0
    db.session.commit()

    response = admin_client.post(
        f'/products/{product.id}/delete',
        follow_redirects=True
    )

    assert response.status_code == 200

    db.session.refresh(product)

    assert product.is_active is False


def test_cannot_delete_product_with_stock(admin_client, product):
    response = admin_client.post(
        f'/products/{product.id}/delete',
        follow_redirects=True
    )

    assert response.status_code == 200

    db.session.refresh(product)

    assert product.is_active is True