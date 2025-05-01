from flask import request, jsonify
from app import app, db
from model import Customer, Menu
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
import os
from model import Orders, OrderItems

# Get all menu items
@app.route('/menu', methods=['GET'])
def get_menu():
    menu = Menu.query.all()
    return jsonify([{"item_id": item.item_id, "name": item.name, "price": str(item.price)} for item in menu])

@app.route("/order", methods=['GET', 'POST'])
def order():
    items = Menu.query.all()  # Fetch all menu items
    if request.method == 'POST':
        print("Form submitted!")  # Debug statement
        print("Form data:", request.form)  # Debug statement

        # Get customer ID and selected items from the form
        customer_id = request.form.get('customer_id')
        selected_items = request.form.getlist('items')  # List of item IDs from the form

        if not customer_id:
            flash("Please enter a customer ID.")
            return redirect(url_for('order'))

        if not selected_items:
            flash("Please select at least one item.")
            return redirect(url_for('order'))

        # Calculate total price
        total_price = 0
        for item_id in selected_items:
            item = Menu.query.get(item_id)
            if item:
                total_price += item.price

        # Create a new order using ORM
        new_order = Orders(customer_id=customer_id, total_price=total_price)
        db.session.add(new_order)
        db.session.commit()  # Commit to generate order_id

        # Add selected items to the order_items table
        for item_id in selected_items:
            item = Menu.query.get(item_id)
            if item:
                order_item = OrderItems(order_id=new_order.order_id, item_id=item.item_id, item_price=item.price)
                db.session.add(order_item)

        db.session.commit()  # Commit the order items

        flash(f"Order placed successfully! Total price: ${total_price:.2f}", "success")
        return redirect(url_for('order_confirmation', order_id=new_order.order_id))  # Redirect to confirmation page

    return render_template("order.html", items=items)


if __name__ == "__main__":
    app.run(debug=True)