from app.models import StockMovement
from app.extensions import db


def test_stock_in(admin_client, product):
    response = admin_client.post(
        f'/products/{product.id}/movement',
        data={
            'movement_type': 'stock_in',
            'qty': '5',
            'reason': 'New stock received'
        },
        follow_redirects=True
    )

    assert response.status_code == 200

    db.session.refresh(product)

    assert product.qty == 15

    movement = db.session.scalar(
        db.select(StockMovement).filter_by(
            product_id=product.id
        )
    )

    assert movement is not None
    assert movement.qty_change == 5


def test_stock_out(admin_client, product):
    response = admin_client.post(
        f'/products/{product.id}/movement',
        data={
            'movement_type': 'stock_out',
            'qty': '3',
            'reason': 'Product issued'
        },
        follow_redirects=True
    )

    assert response.status_code == 200

    db.session.refresh(product)

    assert product.qty == 7


def test_write_off(admin_client, product):
    response = admin_client.post(
        f'/products/{product.id}/movement',
        data={
            'movement_type': 'write_off',
            'qty': '2',
            'reason': 'Damaged products'
        },
        follow_redirects=True
    )

    assert response.status_code == 200

    db.session.refresh(product)

    assert product.qty == 8


def test_stock_adjustment(admin_client, product):
    response = admin_client.post(
        f'/products/{product.id}/movement',
        data={
            'movement_type': 'adjustment',
            'qty': '15',
            'reason': 'Physical stock count'
        },
        follow_redirects=True
    )

    assert response.status_code == 200

    db.session.refresh(product)

    assert product.qty == 15


def test_stock_out_insufficient_quantity(admin_client, product):
    response = admin_client.post(
        f'/products/{product.id}/movement',
        data={
            'movement_type': 'stock_out',
            'qty': '100',
            'reason': 'Testing insufficient stock'
        }
    )

    assert response.status_code == 200

    db.session.refresh(product)

    assert product.qty == 10

    movement = db.session.scalar(
        db.select(StockMovement).filter_by(
            product_id=product.id
        )
    )

    assert movement is None


def test_zero_quantity_stock_in_rejected(admin_client, product):
    response = admin_client.post(
        f'/products/{product.id}/movement',
        data={
            'movement_type': 'stock_in',
            'qty': '0',
            'reason': 'Invalid quantity'
        }
    )

    assert response.status_code == 200

    db.session.refresh(product)

    assert product.qty == 10


def test_negative_adjustment_rejected(admin_client, product):
    response = admin_client.post(
        f'/products/{product.id}/movement',
        data={
            'movement_type': 'adjustment',
            'qty': '-5',
            'reason': 'Invalid adjustment'
        }
    )

    assert response.status_code == 200

    db.session.refresh(product)

    assert product.qty == 10


def test_stock_movement_history(admin_client, product):
    response = admin_client.post(
        f'/products/{product.id}/movement',
        data={
            'movement_type': 'stock_in',
            'qty': '5',
            'reason': 'History test'
        },
        follow_redirects=True
    )

    assert response.status_code == 200

    movement = db.session.scalar(
        db.select(StockMovement).filter_by(
            product_id=product.id
        )
    )

    assert movement is not None
    assert movement.product_id == product.id
    assert movement.qty_before == 10
    assert movement.qty_after == 15


def test_inactive_product_rejects_movement(admin_client, product):
    product.is_active = False
    db.session.commit()

    response = admin_client.post(
        f'/products/{product.id}/movement',
        data={
            'movement_type': 'stock_in',
            'qty': '5',
            'reason': 'Test'
        },
        follow_redirects=True
    )

    assert response.status_code == 200

    db.session.refresh(product)

    assert product.qty == 10