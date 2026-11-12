from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from app.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(150))
    username: Mapped[str] = mapped_column(db.String(50), unique=True)
    email: Mapped[str] = mapped_column(db.String(120), unique=True)
    password_hash: Mapped[str] = mapped_column(db.String(256))    
    role: Mapped[str] = mapped_column(db.String(20), default='employee')
    created_at: Mapped[datetime] = mapped_column(default=lambda:datetime.now(timezone.utc))
    is_active: Mapped[bool] = mapped_column(default=True)

    stock_movements: Mapped[list['StockMovement']] = relationship(back_populates='user')
    

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Products(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(150))
    sku: Mapped[str] = mapped_column(db.String(64), unique=True)
    price: Mapped[float]
    qty: Mapped[int]
    unit: Mapped[str] = mapped_column(db.String(30))
    reorder_level: Mapped[int] = mapped_column(default=5)
    description: Mapped[str | None] = mapped_column(db.String(200))
    created_at: Mapped[datetime] = mapped_column(default=lambda:datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda:datetime.now(timezone.utc))
    is_active: Mapped[bool] = mapped_column(default=True)

    category_id: Mapped[int] = mapped_column(ForeignKey('category.id'))
    category: Mapped['Category'] = relationship(back_populates='products')

    stock_movements: Mapped[list['StockMovement']] = relationship(back_populates='product')


class Category(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), unique=True)

    products: Mapped[list['Products']] = relationship(back_populates='category')


class StockMovement(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    movement_type: Mapped[str] = mapped_column(db.String(20))
    qty_change: Mapped[int]
    qty_before: Mapped[int]
    qty_after: Mapped[int]
    unit: Mapped[str] = mapped_column(db.String(30))
    reason: Mapped[str] = mapped_column(db.Text)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    product: Mapped['Products'] = relationship(back_populates='stock_movements')
    user: Mapped['User'] = relationship(back_populates='stock_movements')


class Invitation(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    code_hash: Mapped[str] = mapped_column(db.String(256), unique=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime]
    used_at: Mapped[datetime | None]
    used_by_id: Mapped[int | None] = mapped_column(ForeignKey('user.id'))
    revoked_at: Mapped[datetime | None]
    revoked_by_id: Mapped[int | None] = mapped_column(ForeignKey('user.id'))
    
    created_by: Mapped['User'] = relationship(foreign_keys=[created_by_id])
    used_by: Mapped['User | None'] = relationship(foreign_keys=[used_by_id])
    revoked_by: Mapped['User | None'] = relationship(foreign_keys=[revoked_by_id])