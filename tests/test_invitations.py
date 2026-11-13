import hashlib

from datetime import datetime, timezone, timedelta

from app.models import Invitation, User
from app.extensions import db


def test_generate_invitation(admin_client):
    admin = db.session.scalar(
        db.select(User).filter_by(username='testadmin')
    )

    response = admin_client.post(
        '/generate-invitation',
        follow_redirects=True
    )

    assert response.status_code == 200

    invitation = db.session.scalar(
        db.select(Invitation).filter_by(
            created_by_id=admin.id
        )
    )

    assert invitation is not None
    assert invitation.code_hash is not None


def test_redeem_invitation(test_app):
    admin = User(
        name='Test Admin',
        username='testadmin',
        email='admin@test.com',
        role='admin'
    )
    admin.set_password('testpassword')

    db.session.add(admin)
    db.session.commit()

    code = 'TEST-INVITATION-123'

    invitation = Invitation(
        code_hash=hashlib.sha256(code.encode()).hexdigest(),
        created_by_id=admin.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
    )

    db.session.add(invitation)
    db.session.commit()

    with test_app.test_client() as anonymous_client:
        response = anonymous_client.post('/register', data={
            'name': 'New Employee',
            'username': 'newemployee',
            'email': 'newemployee@test.com',
            'invitation_code': code,
            'password': 'testpassword',
            'confirm_password': 'testpassword'
        })

    assert response.status_code == 302

    user = db.session.scalar(
        db.select(User).filter_by(username='newemployee')
    )

    assert user is not None
    assert invitation.used_at is not None
    assert invitation.used_by_id == user.id


def test_expired_invitation_rejected(test_app):
    admin = User(
        name='Test Admin',
        username='testadmin',
        email='admin@test.com',
        role='admin'
    )
    admin.set_password('testpassword')

    db.session.add(admin)
    db.session.commit()

    code = 'EXPIRED-INVITATION'

    invitation = Invitation(
        code_hash=hashlib.sha256(code.encode()).hexdigest(),
        created_by_id=admin.id,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
    )

    db.session.add(invitation)
    db.session.commit()

    with test_app.test_client() as anonymous_client:
        response = anonymous_client.post('/register', data={
            'name': 'Expired User',
            'username': 'expireduser',
            'email': 'expired@test.com',
            'invitation_code': code,
            'password': 'testpassword',
            'confirm_password': 'testpassword'
        })

    assert response.status_code == 200

    user = db.session.scalar(
        db.select(User).filter_by(username='expireduser')
    )

    assert user is None


def test_revoke_invitation(admin_client):
    admin = db.session.scalar(
        db.select(User).filter_by(username='testadmin')
    )

    invitation = Invitation(
        code_hash=hashlib.sha256(b'REVOKE-TEST').hexdigest(),
        created_by_id=admin.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
    )

    db.session.add(invitation)
    db.session.commit()

    response = admin_client.post(
        f'/invitation/{invitation.id}/revoke',
        follow_redirects=True
    )

    assert response.status_code == 200

    db.session.refresh(invitation)

    assert invitation.revoked_at is not None
    assert invitation.revoked_by_id == admin.id


def test_used_invitation_cannot_be_revoked(admin_client):
    admin = db.session.scalar(
        db.select(User).filter_by(username='testadmin')
    )

    invitation = Invitation(
        code_hash=hashlib.sha256(b'USED-TEST').hexdigest(),
        created_by_id=admin.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        used_at=datetime.now(timezone.utc)
    )

    db.session.add(invitation)
    db.session.commit()

    response = admin_client.post(
        f'/invitation/{invitation.id}/revoke',
        follow_redirects=True
    )

    assert response.status_code == 200

    db.session.refresh(invitation)

    assert invitation.revoked_at is None