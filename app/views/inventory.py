from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.forms import MovementForm
from app.extensions import db
from app.models import StockMovement, Products

inventory = Blueprint('inventory', __name__)


@inventory.route('/products/<int:product_id>/movement', methods=['GET', 'POST'])
@login_required
def record_movement(product_id):
    product = db.get_or_404(Products, product_id)

    if not product.is_active:
        flash('This product is no longer active,', 'danger')
        return redirect(url_for('products.product_detail', product_id=product.id))
    
    form = MovementForm()

    if form.validate_on_submit():
        movement_type = form.movement_type.data
        qty = form.qty.data

        # throw error if entered data for either stock out or write off is more than qty in the database
        if movement_type in ('stock_out', 'write_off') and qty > product.qty:
            form.qty.errors.append('Insufficient stock.')

        # setting up how qty_change shud look for each movement type
        else:
            if movement_type == 'stock_in':
                qty_change = qty

            elif movement_type == 'stock_out':
                qty_change = -qty

            elif movement_type == 'write_off':
                qty_change = -qty

            elif movement_type == 'adjustment':
                qty_change = qty - product.qty

            qty_before = product.qty
            qty_after = qty_before + qty_change
            product.qty = qty_after

            movement = StockMovement(
                product_id=product.id,
                user_id=current_user.id,
                movement_type=movement_type,
                qty_change=qty_change,
                qty_before=qty_before,
                qty_after=qty_after,
                unit=product.unit,
                reason=form.reason.data
            )

            db.session.add(movement)

            # this commits both product.qty = qty_after as the updated product.qty and StockMovement record
            db.session.commit()

            flash('Stock movement recorded successfully', 'success')
            return redirect(url_for('products.product_detail', product_id=product.id))

    return render_template('record_movement.html', form=form, product=product)