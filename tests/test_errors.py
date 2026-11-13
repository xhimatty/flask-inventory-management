from flask import abort
from app import app


@app.route('/test-error-400')
def trigger_error_400_route():
    abort(400)


@app.route('/test-error-403')
def trigger_error_403_route():
    abort(403)


@app.route('/test-error-405', methods=['POST'])
def trigger_error_405_route():
    return 'OK'


@app.route('/test-error-500')
def trigger_error_500_route():
    raise RuntimeError('Testing internal server error')


def test_bad_request(client):
    response = client.get('/test-error-400')

    assert response.status_code == 400


def test_forbidden(client):
    response = client.get('/test-error-403')

    assert response.status_code == 403


def test_not_found(client):
    response = client.get('/this-page-does-not-exist')

    assert response.status_code == 404


def test_method_not_allowed(client):
    response = client.get('/test-error-405')

    assert response.status_code == 405


def test_internal_server_error(client):
    client.application.config['PROPAGATE_EXCEPTIONS'] = False

    response = client.get('/test-error-500')

    assert response.status_code == 500