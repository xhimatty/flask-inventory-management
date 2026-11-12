import json
from app import app
from app.extensions import db
from app.models import Products, Category
from sqlalchemy import select

with app.app_context():
    stmt = select(Category)
    categories = {c.name: c for c in db.session.scalars(stmt)}

    with open("product.json", encoding="utf-8") as f:
        items = json.load(f)

    for item in items:
        db.session.add(Products(
            name=item["name"],
            sku=item["sku"],
            price=item["price"],
            qty=item["qty"],
            unit=item["unit"],
            description=item["description"],
            category=categories[item["category"]],
        ))

    db.session.commit()
    print(f"Added {len(items)} products.")