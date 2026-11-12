from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, EmailField, PasswordField, SubmitField, IntegerField, DecimalField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo, Email, ValidationError, NumberRange, Optional, InputRequired
from app.extensions import db
from app.models import User
from sqlalchemy import select

class RegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired(), Length(min=4)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    invitation_code = StringField('Invitation Code', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=4, max=30)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Create Account')

    def validate_username(self, username):
        stmt = select(User).filter_by(username=username.data.strip())
        existing_user = db.session.scalar(stmt)

        if existing_user:
            raise ValidationError('Username already exists')

    def validate_email(self, email):
        stmt = select(User).filter_by(email=email.data.strip().lower())
        existing_email = db.session.scalar(stmt)

        if existing_email:
            raise ValidationError('Email already exists')


class ChangeUsernameForm(FlaskForm):
    username = StringField('New Username', validators=[DataRequired(), Length(min=4)])
    submit = SubmitField('Change Username')

    def validate_username(self, username):
        if username.data.strip() == current_user.username:
            raise ValidationError('New username cannot be the same as the current username')

        stmt = select(User).filter_by(username=username.data.strip())
        existing_user = db.session.scalar(stmt)

        if existing_user:
            raise ValidationError('Username already exists')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=4, max=30)])
    submit = SubmitField('Change Password')

    def validate_current_password(self, current_password):
        if not current_user.check_password(current_password.data):
            raise ValidationError('Incorrect current password')

    def validate_password(self, password):
        if current_user.check_password(password.data):
            raise ValidationError('New password cannot be the same as the current password')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')


class AddProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired(), Length(min=2, max=150)])
    sku = StringField('SKU', validators=[DataRequired(), Length(min=4, max=64)])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    price = DecimalField('Price', validators=[DataRequired(), NumberRange(min=0.01)])
    qty = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=0)])
    unit = StringField('Unit', validators=[DataRequired(), Length(max=30)])
    reorder_level = IntegerField('Reorder Level', validators=[Optional(), NumberRange(min=0)], default=5)
    description = TextAreaField('Description', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Add Product')


class EditProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired(), Length(min=2, max=150)])
    sku = StringField('SKU', validators=[DataRequired(), Length(min=4, max=64)])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    price = DecimalField('Price', validators=[DataRequired(), NumberRange(min=0.01)])
    unit = StringField('Unit', validators=[DataRequired(), Length(max=30)])
    reorder_level = IntegerField('Reorder Level', validators=[Optional(), NumberRange(min=0)], default=5)
    description = TextAreaField('Description', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Update Product')


class MovementForm(FlaskForm):
    movement_type = SelectField('Movement Type', choices=[('', 'Select movement type'), ('stock_in', 'Stock In'), ('stock_out', 'Stock Out'), ('adjustment', 'Adjustment'), ('write_off', 'Write Off')], validators=[DataRequired()])
    qty = IntegerField('Quantity', validators=[InputRequired(), NumberRange(min=0)])
    reason = TextAreaField('Reason', validators=[DataRequired()])
    submit = SubmitField('Record Movement')

    def validate_qty(self, qty):
        if self.movement_type.data == 'adjustment':
            if qty.data < 0:
                raise ValidationError('Physical stock count cannot be negative.')
            
        # validation error if data entered for qty for (stock in, stock out, and write off) is less than 0
        else:
            if qty.data <= 0:
                raise ValidationError('Quantity must be greater than zero.')
    