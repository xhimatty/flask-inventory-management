def test_login_page_loads(client):
    response = client.get('/login')

    assert response.status_code == 200


def test_products_requires_login(client):
    response = client.get('/products')

    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_employee_cannot_access_employees_page(employee_client):
    response = employee_client.get('/employees')

    assert response.status_code == 403


def test_admin_can_access_employees_page(admin_client):
    response = admin_client.get('/employees')

    assert response.status_code == 200


def test_login_with_invalid_credentials(client):
    response = client.post('/login', data={
        'username': 'wronguser',
        'password': 'wrongpassword'
    })

    assert response.status_code == 200
    assert b'Invalid username or password' in response.data