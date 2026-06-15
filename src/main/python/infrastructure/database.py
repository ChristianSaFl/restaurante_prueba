from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ── Models ────────────────────────────────────────────────────────────────────

class UserModel(db.Model):
    __tablename__ = "users"
    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(80), unique=True, nullable=False)
    password   = db.Column(db.String(200), nullable=False)
    role       = db.Column(db.String(20), default="staff")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CategoryModel(db.Model):
    __tablename__ = "categories"
    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)


class ProductModel(db.Model):
    __tablename__ = "products"
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(120), nullable=False)
    price       = db.Column(db.Float, nullable=False)
    category    = db.Column(db.String(60), default="General")
    description = db.Column(db.String(300), nullable=True)
    available   = db.Column(db.Boolean, default=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)


class TableModel(db.Model):
    __tablename__ = "tables"
    id       = db.Column(db.Integer, primary_key=True)
    number   = db.Column(db.Integer, unique=True, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    occupied = db.Column(db.Boolean, default=False)
    location = db.Column(db.String(60), nullable=True)   # ej: "Terraza", "Interior"


class OrderModel(db.Model):
    __tablename__ = "orders"
    id         = db.Column(db.Integer, primary_key=True)
    table_id   = db.Column(db.Integer, db.ForeignKey("tables.id"), nullable=True)
    status     = db.Column(db.String(20), default="open")
    notes      = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items      = db.relationship("OrderItemModel", backref="order", lazy=True, cascade="all, delete-orphan")
    table      = db.relationship("TableModel", backref="orders")

    def total(self):
        return sum(i.subtotal() for i in self.items)

    def is_empty(self):
        return len(self.items) == 0


class OrderItemModel(db.Model):
    __tablename__ = "order_items"
    id         = db.Column(db.Integer, primary_key=True)
    order_id   = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity   = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    notes      = db.Column(db.String(200), nullable=True)
    product    = db.relationship("ProductModel")

    def subtotal(self):
        return self.unit_price * self.quantity


class BillModel(db.Model):
    __tablename__ = "bills"
    id                  = db.Column(db.Integer, primary_key=True)
    order_id            = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    discount_percentage = db.Column(db.Float, default=0)
    tip                 = db.Column(db.Float, default=0)
    payment_method      = db.Column(db.String(30), default="efectivo")
    paid                = db.Column(db.Boolean, default=False)
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at             = db.Column(db.DateTime, nullable=True)
    order               = db.relationship("OrderModel")

    TAX_RATE     = 0.18
    MAX_DISCOUNT = 50

    def subtotal(self):
        return self.order.total()

    def discount_amount(self):
        return self.subtotal() * self.discount_percentage / 100

    def tax(self):
        return (self.subtotal() - self.discount_amount()) * self.TAX_RATE

    def total(self):
        return (self.subtotal() - self.discount_amount()) + self.tax() + self.tip


class ReservationModel(db.Model):
    __tablename__ = "reservations"
    id           = db.Column(db.Integer, primary_key=True)
    customer_name= db.Column(db.String(120), nullable=False)
    customer_phone=db.Column(db.String(20), nullable=True)
    table_id     = db.Column(db.Integer, db.ForeignKey("tables.id"), nullable=True)
    guests       = db.Column(db.Integer, nullable=False)
    date         = db.Column(db.Date, nullable=False)
    time         = db.Column(db.String(10), nullable=False)
    status       = db.Column(db.String(20), default="pending")  # pending/confirmed/cancelled
    notes        = db.Column(db.String(300), nullable=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    table        = db.relationship("TableModel", backref="reservations")
