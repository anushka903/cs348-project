from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
import os
import random
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user

#from flask_mysqldb import MySQL


app = Flask(__name__)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Securely fetch database credentials from environment variables
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'California#77')
CLOUD_SQL_IP = os.getenv('CLOUD_SQL_IP', '34.135.140.218')
DB_NAME = os.getenv('DB_NAME', 'coffee_cafe')

# Configure the database URI
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{CLOUD_SQL_IP}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Secret key for Flask-WTF and flash messages
app.config['SECRET_KEY'] = 'your_secret_key_here'

# Initialize the database
db = SQLAlchemy(app)

@login_manager.user_loader
def load_user(customer_id):
    return Customer.query.get(int(customer_id))

class Customer(db.Model):
    __tablename__ = 'customer'
    customer_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    phone = db.Column(db.String(15), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128))

    @property
    def is_active(self):
        """All users are active by default"""
        return True

    @property
    def is_authenticated(self):
        """Return True if the user is authenticated"""
        return True

    @property
    def is_anonymous(self):
        """False as we don't support anonymous users"""
        return False

    # Required method for Flask-Login
    def get_id(self):
        """Return the customer_id to satisfy Flask-Login's requirements"""
        return str(self.customer_id)

    # Your existing password methods
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Menu(db.Model):
    __tablename__ = 'menu'
    item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    price = db.Column(db.Numeric(10,2), nullable=False)
    category = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)

class Orders(db.Model):
    __tablename__ = 'orders'
    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.customer_id'), nullable=True)
    order_time = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=True)
    total_price = db.Column(db.Numeric(8, 2), nullable=False)
    order_items = db.relationship('OrderItems', back_populates='orders')

class OrderItems(db.Model):
    __tablename__ = 'order_items'
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('menu.item_id'), primary_key=True)
    orders = db.relationship('Orders', back_populates='order_items')
    menu = db.relationship('Menu', backref='order_items')

# Create form class
class UserForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    phone = StringField("Phone", validators=[DataRequired()])
    password = StringField("Password", validators=[DataRequired()])
    submit = SubmitField("Submit")

@app.route("/order_confirmation/<int:order_id>")
def order_confirmation(order_id):
    # Fetch the order details
    order = Orders.query.get(order_id)
    if not order:
        flash("Order not found.")
        return redirect(url_for('home'))

    # Fetch the items in the order
    order_items = OrderItems.query.filter_by(order_id=order_id).all()
    items = []
    for order_item in order_items:
        item = Menu.query.get(order_item.item_id)
        if item:
            items.append({"name": item.name, "price": item.price})

    return render_template("order_confirmation.html", order=order, items=items)


# Root route
@app.route("/")
def home():
    return render_template("index.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        customer = Customer.query.filter_by(email=email).first()

        if not customer or not customer.check_password(password):
            flash('Please check your login details and try again.')
            return redirect(url_for('login'))

        login_user(customer, remember=remember)
        return redirect(url_for('profile'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/profile')
@login_required
def profile():
    # Get all orders for the current user
    orders = Orders.query.filter_by(customer_id=current_user.customer_id).all()

    order_details = []
    for order in orders:
        # Get all order items for this order
        order_items = OrderItems.query.filter_by(order_id=order.order_id).all()

        # Fetch item names from Menu table
        item_names = []
        for order_item in order_items:
            menu_item = Menu.query.get(order_item.item_id)
            if menu_item:
                item_names.append(menu_item.name)

        order_details.append({
            'order': order,
            'item_names': item_names  # Changed from 'items' to 'item_names'
        })

    return render_template("profile.html", order_details=order_details)

@app.route('/menu')
def menu():
    # Fetch all menu items from the database
    menu_items = Menu.query.all()

    # Group items by category
    items_by_category = {}
    for item in menu_items:
        if item.category not in items_by_category:
            items_by_category[item.category] = []
        items_by_category[item.category].append(item)

    # Pass the grouped menu items to the template
    return render_template('menu.html', items_by_category=items_by_category)

@app.route("/order", methods=['GET', 'POST'])
@login_required
def order():
    items = Menu.query.all()  # Fetch all menu items
    if request.method == 'POST':
        # Automatically use the logged-in customer's ID
        customer_id = current_user.customer_id
        selected_items = request.form.getlist('items')

        if not selected_items:
            flash("Please select at least one item.", "error")
            return redirect(url_for('order'))

        # Calculate total price
        total_price = sum(
            float(Menu.query.get(item_id).price)
            for item_id in selected_items
            if Menu.query.get(item_id)
        )

        # Create and save the order
        new_order = Orders(customer_id=customer_id, total_price=total_price)
        db.session.add(new_order)
        db.session.flush()  # Get the order_id without committing

        # Add order items
        for item_id in selected_items:
            if Menu.query.get(item_id):
                db.session.add(OrderItems(
                    order_id=new_order.order_id,
                    item_id=item_id
                ))

        db.session.commit()
        flash(f"Order placed successfully! Total: ${total_price:.2f}", "success")
        return redirect(url_for('order_confirmation', order_id=new_order.order_id))

    return render_template("order.html", items=items)

@app.route("/generate_report", methods=['GET', 'POST'])
@login_required
def generate_report():
    if request.method == 'POST':
        # Get filter criteria from the form
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        customer_id = request.form.get('customer_id')
        item_id = request.form.get('item_id')

        # Build the base query using prepared statements
        query = text("""
            SELECT * FROM orders
            WHERE 1=1
            AND (:start_date IS NULL OR order_time >= :start_date)
            AND (:end_date IS NULL OR order_time <= :end_date)
            AND (:customer_id IS NULL OR customer_id = :customer_id)
        """)

        # Execute the query with parameters
        orders = db.session.execute(query, {
            "start_date": start_date,
            "end_date": end_date,
            "customer_id": customer_id
        }).fetchall()

        # Extract order IDs
        order_ids = [order.order_id for order in orders]

        # Fetch order_items only if there are orders
        order_items = []
        if order_ids:  # Check if order_ids is not empty
            order_items_query = text("""
                SELECT * FROM order_items
                WHERE order_id IN :order_ids
            """)
            order_items = db.session.execute(order_items_query, {
                "order_ids": tuple(order_ids)  # Convert to tuple for SQL IN clause
            }).fetchall()

        # Calculate report statistics
        total_revenue = sum(order.total_price for order in orders)
        average_order_value = total_revenue / len(orders) if orders else 0
        num_orders = len(orders)

        # Find the most popular item
        from collections import defaultdict
        item_counts = defaultdict(int)
        for order_item in order_items:
            item_counts[order_item.item_id] += 1

        most_popular_item_id = max(item_counts, key=item_counts.get) if item_counts else None
        most_popular_item = Menu.query.get(most_popular_item_id) if most_popular_item_id else None

        # Render the report template with the results
        return render_template("report_results.html",
                              orders=orders,
                              total_revenue=total_revenue,
                              average_order_value=average_order_value,
                              num_orders=num_orders,
                              most_popular_item=most_popular_item)

    # Fetch all menu items for the dropdown
    menu_items = Menu.query.all()
    return render_template("report.html", menu_items=menu_items)

@app.route("/register_customer", methods=['GET', 'POST'])
def register_customer():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')

        # Check if email already exists
        if Customer.query.filter_by(email=email).first():
            flash('Email address already exists')
            return redirect(url_for('register_customer'))

        # Generate a unique customer ID
        while True:
            customer_id = random.randint(1000, 9999)
            if not Customer.query.get(customer_id):
                break

        # Create new customer with hashed password
        new_customer = Customer(
            customer_id=customer_id,
            name=name,
            email=email,
            phone=phone
        )
        new_customer.set_password(password)

        db.session.add(new_customer)
        db.session.commit()

        # Log the user in after registration
        login_user(new_customer)
        return redirect(url_for('profile'))

    # For GET requests, fetch all customers and pass to template
    all_customers = Customer.query.all()
    return render_template("register_customer.html", all_customers=all_customers)

@app.route("/delete_customer/<int:customer_id>", methods=['POST'])
@login_required
def delete_customer(customer_id):
    # Find the customer by ID
    customer = Customer.query.get(customer_id)

    if customer:
        try:
            # Delete all orders associated with the customer
            Orders.query.filter_by(customer_id=customer_id).delete()

            # Delete the customer
            db.session.delete(customer)
            db.session.commit()
            return jsonify({"success": True, "message": "Customer and associated orders deleted successfully"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": f"An error occurred: {str(e)}"}), 500
    else:
        return jsonify({"success": False, "message": "Customer not found"}), 404


@app.route("/edit_order/<int:order_id>", methods=['GET', 'POST'])
@login_required
def edit_order(order_id):
    # Fetch the order and its associated items
    order = Orders.query.get_or_404(order_id)
    order_items = OrderItems.query.filter_by(order_id=order_id).all()
    menu_items = Menu.query.all()  # Fetch all menu items for the form

    if request.method == 'POST':
        # Get updated customer ID and selected items from the form
        customer_id = request.form.get('customer_id')
        selected_items = request.form.getlist('items')  # List of item IDs from the form

        if not customer_id:
            flash("Please enter a customer ID.")
            return redirect(url_for('edit_order', order_id=order_id))

        if not selected_items:
            flash("Please select at least one item.")
            return redirect(url_for('edit_order', order_id=order_id))

        # Calculate total price
        total_price = 0
        for item_id in selected_items:
            item = Menu.query.get(item_id)
            if item:
                total_price += item.price

        # Update the order using prepared statements
        update_order_query = text("""
            UPDATE orders
            SET customer_id = :customer_id, total_price = :total_price
            WHERE order_id = :order_id
        """)
        db.session.execute(update_order_query, {
            "customer_id": customer_id,
            "total_price": total_price,
            "order_id": order_id
        })

        # Delete existing order items using prepared statements
        delete_order_items_query = text("""
            DELETE FROM order_items
            WHERE order_id = :order_id
        """)
        db.session.execute(delete_order_items_query, {"order_id": order_id})

        # Add new order items using prepared statements
        insert_order_item_query = text("""
            INSERT INTO order_items (order_id, item_id)
            VALUES (:order_id, :item_id)
        """)
        for item_id in selected_items:
            db.session.execute(insert_order_item_query, {
                "order_id": order_id,
                "item_id": item_id
            })

        db.session.commit()  # Commit the changes

        flash("Order updated successfully!", "success")
        return redirect(url_for('order_confirmation', order_id=order.order_id))

    # Pre-select the items in the order
    selected_item_ids = [item.item_id for item in order_items]

    return render_template("edit_order.html", order=order, menu_items=menu_items, selected_item_ids=selected_item_ids)


@app.route("/delete_account", methods=['POST'])
@login_required
def delete_account():
    try:
        customer_id = current_user.customer_id

        # First delete order_items associated with the customer's orders
        order_ids = [order.order_id for order in Orders.query.filter_by(customer_id=customer_id).all()]
        if order_ids:
            OrderItems.query.filter(OrderItems.order_id.in_(order_ids)).delete()

        # Then delete the orders
        Orders.query.filter_by(customer_id=customer_id).delete()

        # Finally delete the customer
        db.session.delete(current_user)
        db.session.commit()

        logout_user()
        return jsonify({
            "success": True,
            "message": "Your account has been permanently deleted."
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"An error occurred: {str(e)}"
        }), 500
@app.route("/edit_account", methods=['GET', 'POST'])
@login_required
def edit_account():
    if request.method == 'POST':
        # Get form data
        current_user.name = request.form.get('name', current_user.name)
        current_user.email = request.form.get('email', current_user.email)
        current_user.phone = request.form.get('phone', current_user.phone)

        # Handle password change if provided
        new_password = request.form.get('new_password')
        if new_password:
            current_user.set_password(new_password)

        db.session.commit()
        flash('Account updated successfully!', 'success')
        return redirect(url_for('profile'))

    return render_template("edit_account.html", user=current_user)
if __name__ == "__main__":
    # Run Flask on 0.0.0.0 to allow external access (e.g., from Google Cloud)
    app.run(host="0.0.0.0", port=8080, debug=True)