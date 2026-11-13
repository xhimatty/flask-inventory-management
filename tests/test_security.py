from app.models import User
from app.extensions import db


def test_unauthenticated_user_cannot_access_products(client):
    response = client.get('/products')

    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_unauthenticated_user_cannot_access_profile(client):
    response = client.get('/profile')

    assert response.status_code == 302


def test_inactive_user_cannot_login(client):
    user = User(
        name='Inactive User',
        username='inactiveuser',
        email='inactive@test.com',
        is_active=False
    )

    user.set_password('testpassword')

    db.session.add(user)
    db.session.commit()

    response = client.post('/login', data={
        'username': 'inactiveuser',
        'password': 'testpassword'
    })

    assert response.status_code == 200
    assert b'Invalid username or password' in response.data


def test_employee_cannot_generate_invitation(employee_client):
    response = employee_client.post('/generate-invitation')

    assert response.status_code == 403


def test_employee_cannot_revoke_invitation(employee_client):
    response = employee_client.post('/invitation/1/revoke')

    assert response.status_code == 403


def test_logout(admin_client):
    response = admin_client.get('/logout')

    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_csrf_protection(client, monkeypatch):
    monkeypatch.setitem(
        client.application.config,
        'WTF_CSRF_ENABLED',
        True
    )

    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    })

    assert response.status_code == 400