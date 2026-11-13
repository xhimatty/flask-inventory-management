from flask import Blueprint, render_template, redirect, flash, url_for, abort, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app.forms import RegistrationForm, LoginForm, ChangeUsernameForm, ChangePasswordForm
from app.models import User, Invitation
from app.extensions import db
from sqlalchemy import select
from functools import wraps
import secrets
import hashlib
from datetime import datetime, timezone, timedelta

auth = Blueprint('auth', __name__)


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        code_hash = hashlib.sha256(form.invitation_code.data.encode()).hexdigest()

        stmt = select(Invitation).where(Invitation.code_hash == code_hash)
        invitation = db.session.scalar(stmt)

        if not invitation:
            flash('Invalid invitation code', 'danger')
            return render_template('register.html', form=form)

        if invitation.used_at is not None:
            flash('This invitation code has already been used', 'danger')
            return render_template('register.html', form=form)

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        if invitation.expires_at <= now:
            flash('This invitation code has expired', 'danger')
            return render_template('register.html', form=form)

        user = User(
            name=form.name.data.strip(),
            username=form.username.data.strip(),
            email=form.email.data.strip().lower()
        )

        user.set_password(form.password.data)

        db.session.add(user)
        db.session.flush()

        invitation.used_at = datetime.now(timezone.utc)
        invitation.used_by_id = user.id
        
        db.session.commit()

        flash('Account created successfully!', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html', form=form)


@auth.route('/change-username', methods=['GET', 'POST'])
@login_required
def change_username():
    form = ChangeUsernameForm()

    if form.validate_on_submit():
        current_user.username = form.username.data.strip()

        db.session.commit()

        flash('Username updated successfully!', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('change_username.html', form=form)


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        current_user.set_password(form.password.data)

        db.session.commit()

        flash('Password updated successfully!', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('change_password.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        stmt = select(User).filter_by(username=form.username.data.strip())
        user = db.session.scalar(stmt)

        if user and user.is_active and user.check_password(form.password.data):
            login_user(user)
            session.permanent = True

            flash('Login successful', 'success')
            return redirect(url_for('main.home'))

        flash('Invalid username or password', 'danger')

    return render_template('login.html', form=form)


@auth.route('/logout')
def logout():
    logout_user()
    flash('Logout successful', 'success')
    return redirect(url_for('auth.login'))


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped_view(*args, **kwargs):
        if current_user.role != 'admin':
            abort(403)

        return view(*args, **kwargs)
    
    return wrapped_view


@auth.route('/employees')
@admin_required
def employees():
    stmt = select(User).filter_by(role='employee').order_by(User.created_at.desc())
    employees = db.session.scalars(stmt).all()

    invitation_stmt = select(Invitation).order_by(Invitation.created_at.desc())
    invitations = db.session.scalars(invitation_stmt).all()

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    return render_template(
        'employees.html', 
        employees=employees, 
        invitations=invitations,
        now=now
    )


@auth.route('/generate-invitation', methods=['POST'])
@admin_required
def generate_invitation():
    code = secrets.token_urlsafe(16)
    code_hash = hashlib.sha256(code.encode()).hexdigest()

    invitation = Invitation(
        code_hash=code_hash,
        created_by_id=current_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
    )

    db.session.add(invitation)
    db.session.commit()

    return render_template(
        'invitation_generated.html',
        code=code
    )


@auth.route('/invitation/<int:invitation_id>/revoke', methods=['POST'])
@admin_required
def revoke_invitation(invitation_id):
    invitation = db.get_or_404(Invitation, invitation_id)

    if invitation.revoked_at:
        flash('This invitation code has already been revoked', 'warning')
        return redirect(url_for('auth.employees'))

    if invitation.used_at:
        flash('Used invitations code cannot be revoked', 'danger')
        return redirect(url_for('auth.employees'))

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if invitation.expires_at <= now:
        flash('Expired invitations code cannot be revoked', 'warning')
        return redirect(url_for('auth.employees'))

    invitation.revoked_at = datetime.now(timezone.utc)
    invitation.revoked_by = current_user

    db.session.commit()

    flash('Invitation successfully revoked', 'success')
    return redirect(url_for('auth.employees'))


@auth.route('/employees/<int:employee_id>/status', methods=['POST'])
@admin_required
def update_employee_status(employee_id):
    employee = db.get_or_404(User, employee_id)

    if employee.role != 'employee':
        abort(404)

    action = request.form.get('action')

    if action == 'deactivate':
        employee.is_active = False
        flash(f'{employee.name} account has been deactivated', 'success')

    elif action == 'activate':
        employee.is_active = True
        flash(f'{employee.name} account has been activated', 'success')

    else:
        abort(404)

    db.session.commit()

    return redirect(url_for('auth.employees'))


@auth.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)