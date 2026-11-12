from datetime import datetime
from flask import Blueprint, render_template
from sqlalchemy import select, func
from app.extensions import db
from app.models import Products, StockMovement

main = Blueprint('main', __name__)


@main.route('/')
def home():

    current_hour = datetime.now().hour
    
    if current_hour < 12:
        greeting = 'Good morning'
    elif current_hour < 17:
        greeting = 'Good afternoon'
    else:
        greeting = 'Good evening'
    
    date_today = datetime.today().strftime('%A, %d %B, %Y')

    # Total active products
    total_products = db.session.scalar(
        select(func.count(Products.id)).where(
            Products.is_active.is_(True)
        )
    )

    # Total low stock products
    low_stock = db.session.scalar(
        select(func.count(Products.id)).where(
            Products.is_active.is_(True),
            Products.qty > 0,
            Products.qty <= Products.reorder_level
        )
    )

    # Out of stock products
    out_of_stock = db.session.scalar(
        select(func.count(Products.id)).where(
            Products.is_active.is_(True),
            Products.qty == 0
        )
    )

    # Low stock products
    low_stock_products = db.session.scalars(
        select(Products).where(
            Products.is_active.is_(True),
            Products.qty > 0,
            Products.qty <= Products.reorder_level
        ).order_by(Products.qty.asc()).limit(5)
    ).all()

    out_of_stock_products = db.session.scalars(
        select(Products).where(
            Products.is_active.is_(True),
            Products.qty == 0
        ).order_by(Products.qty.asc()).limit(5)
    ).all()

    # Recent stock movements
    recent_movements = db.session.scalars(
        select(StockMovement).order_by(StockMovement.created_at.desc()).limit(10)
    ).all()

    return render_template(
        'home.html', 
        total_products=total_products, 
        low_stock=low_stock, 
        out_of_stock=out_of_stock,
        low_stock_products=low_stock_products,
        out_of_stock_products=out_of_stock_products,
        recent_movements=recent_movements,
        date_today=date_today,
        greeting=greeting
    )