from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Barista(db.Model):
    __tablename__ = 'barista'
    barista_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)

class Customer(db.Model):
    __tablename__ = 'customer'
    customer_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)

class Menu(db.Model):
    __tablename__ = 'menu'
    item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)

class OrderItems(db.Model):
    __tablename__ = 'order_items'
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('menu.item_id'), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Numeric(8, 2), nullable=False)

class Orders(db.Model):
    __tablename__ = 'orders'
    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.customer_id'), nullable=True)
    barista_id = db.Column(db.Integer, db.ForeignKey('barista.barista_id'), nullable=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.payment_id'), nullable=True)
    order_time = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=True)
    total_price = db.Column(db.Numeric(8, 2), nullable=False)

class Payments(db.Model):
    __tablename__ = 'payments'
    payment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    payment_time = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=True)
    amount = db.Column(db.Numeric(8, 2), nullable=False)
    payment_method = db.Column(db.Text, nullable=False)