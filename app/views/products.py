from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required
from app.forms import AddProductForm, EditProductForm
from app.models import Products, Category, StockMovement
from sqlalchemy import select, or_
from app.extensions import db
from datetime import datetime, timezone

prod = Blueprint('products', __name__)



@prod.route('/products')
@login_required
def products():
    search = request.args.get('search', '').strip()

    stmt = select(Products).where(Products.is_active.is_(True))

    if search:
        stmt = stmt.where(
            or_(
                Products.name.ilike(f'%{search}%'),
                Products.sku.ilike(f'%{search}%'),
                Products.description.ilike(f'%{search}%'),
            )
        )

    category_id = request.args.get('category', type=int)

    if category_id:
        stmt = stmt.where(Products.category_id == category_id)

    stock_status = request.args.get('status', '')

    if stock_status == 'in_stock':
        stmt = stmt.where(Products.qty > Products.reorder_level)
    elif stock_status == 'low_stock':
        stmt = stmt.where(Products.qty > 0, Products.qty <= Products.reorder_level)
    elif stock_status == 'out_of_stock':
        stmt = stmt.where(Products.qty == 0)

    pagination = db.paginate(stmt, per_page=10)

    stmt_ = select(Category)
    categories = db.session.scalars(stmt_).all()

    return render_template(
        'products.html', 
        products=pagination.items, 
        search=search, 
        pagination=pagination, 
        category_id=category_id, 
        categories=categories, 
        stock_status=stock_status
    )


@prod.route('/products/inactive')
@login_required
def inactive_products():
    stmt = select(Products).where(
        Products.is_active.is_(False)
    ).order_by(Products.created_at.desc())

    products = db.session.scalars(stmt).all()

    return render_template(
        'inactive_products.html',
        products=products
    )


@prod.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    form = AddProductForm()

    stmt = select(Category).order_by(Category.name)
    categories = db.session.scalars(stmt).all()
    form.category_id.choices = [(0, 'Select Category')] + [(category.id, category.name) for category in categories]

    if form.validate_on_submit():
        product = Products(
            name = form.name.data.strip(),
            sku = form.sku.data.strip(),
            price = form.price.data,
            qty = form.qty.data,
            unit = form.unit.data.strip(),
            reorder_level = form.reorder_level.data,
            description = form.description.data.strip(),
            category_id = form.category_id.data
        )

        db.session.add(product)
        db.session.commit()

        flash('Product added successfully', 'success')
        return redirect(url_for('products.products', product=product))

    return render_template('add_product.html', form=form)


@prod.route('/products/<int:product_id>')
@login_required
def product_detail(product_id):
    product = db.get_or_404(Products, product_id)

    stmt = select(StockMovement).where(StockMovement.product_id == product.id).order_by(StockMovement.created_at.desc())
    movements = db.session.scalars(stmt).all()

    return render_template('product_detail.html', product=product, movements=movements)


@prod.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = db.get_or_404(Products, product_id)

    form = EditProductForm(obj=product)

    stmt = select(Category).order_by(Category.name)
    categories = db.session.scalars(stmt).all()
    form.category_id.choices = [(category.id, category.name) for category in categories]

    if form.validate_on_submit():
        product.name = form.name.data.strip()
        product.sku = form.sku.data.strip()
        product.category_id = form.category_id.data
        product.price = form.price.data
        product.unit = form.unit.data.strip()
        product.description = form.description.data.strip()

        if form.reorder_level is not None:
            product.reorder_level = form.reorder_level.data

        product.updated_at = datetime.now(timezone.utc)

        db.session.commit()

        flash('Product updated successfully!', 'success')
        return redirect(url_for('products.products'))

    return render_template('edit_product.html', product=product, form=form)


@prod.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    product = db.get_or_404(Products, product_id)

    if product.qty > 0:
        flash('Cannot delete a product that is in stock', 'danger')
        return redirect(url_for('products.products'))
    
    product.is_active = False
    db.session.commit()

    flash('Product deleted successfully!', 'success')
    return redirect(url_for('products.products'))


@prod.route('/products/<int:product_id>/status', methods=['POST'])
@login_required
def update_product_status(product_id):
    product = db.get_or_404(Products, product_id)

    action = request.form.get('action')

    if action == 'deactivate':
        product.is_active = False
        flash(f'{product.name} has been deactivated', 'success')

    elif action == 'activate':
        product.is_active = True
        flash(f'{product.name} has been activated', 'success')

    else:
        abort(404)

    db.session.commit()

    return redirect(url_for('products.products'))