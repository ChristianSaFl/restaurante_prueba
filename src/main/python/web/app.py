import os

from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from functools import wraps
from datetime import datetime, timedelta, date, timezone
from dotenv import load_dotenv
load_dotenv()
from werkzeug.security import generate_password_hash, check_password_hash

from src.main.python.infrastructure.database import (
    db, UserModel, ProductModel, TableModel,
    OrderModel, OrderItemModel, BillModel, ReservationModel
)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

ORDER_CREATE_TEMPLATE = "orders/create.html"
RESERVATION_CREATE_TEMPLATE = "reservations/create.html"
DATE_FORMAT = "%Y-%m-%d"


def get_required_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Falta configurar la variable de entorno: {name}")
    return value


def create_seed_user(username, env_name, role):
    password = get_required_env(env_name)
    return UserModel(
        username=username,
        password=generate_password_hash(password),
        role=role
    )



def seed():
    if not UserModel.query.first():
        db.session.add(create_seed_user("admin", "ADMIN_INITIAL_PASSWORD", "admin"))
        db.session.add(create_seed_user("staff", "STAFF_INITIAL_PASSWORD", "staff"))

    if not ProductModel.query.first():
        for p in [
            ("Pizza Margherita", 25, "Pizzas", "Pizza clásica con tomate y mozzarella"),
            ("Pizza Pepperoni",  28, "Pizzas", "Pizza con pepperoni importado"),
            ("Hamburguesa Classic", 18, "Hamburguesas", "Con lechuga, tomate y papas"),
            ("Hamburguesa BBQ",  22, "Hamburguesas", "Con salsa BBQ y aros de cebolla"),
            ("Coca Cola",   7,  "Bebidas", "350ml"),
            ("Jugo Natural", 9, "Bebidas", "Naranja, mango o maracuyá"),
            ("Agua Mineral", 5, "Bebidas", "500ml con o sin gas"),
            ("Ensalada César", 15, "Ensaladas", "Con pollo, crutones y aderezo"),
            ("Lomo Saltado",   32, "Platos", "Tradicional con arroz y papas fritas"),
            ("Pollo a la Brasa", 38, "Platos", "Medio pollo con papas y ensalada"),
            ("Tiramisú",    14, "Postres", "Clásico italiano"),
            ("Cheesecake",  12, "Postres", "Con frutos rojos"),
        ]:
            db.session.add(ProductModel(name=p[0], price=p[1], category=p[2], description=p[3]))

    if not TableModel.query.first():
        for n, c, loc in [
            (1, 4, "Interior"),
            (2, 2, "Terraza"),
            (3, 6, "Interior"),
            (4, 4, "Terraza"),
            (5, 8, "Salón privado"),
            (6, 2, "Barra")
        ]:
            db.session.add(TableModel(number=n, capacity=c, location=loc))

    db.session.commit()


def initialize_database():
    with app.app_context():
        db.create_all()
        seed()


def _clear_products():
    """Elimina todos los productos. Utilidad para tests funcionales (Selenium)
    que necesitan partir de un estado limpio antes de cada caso de prueba."""
    with app.app_context():
        ProductModel.query.delete()
        db.session.commit()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Inicia sesión para continuar.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        user = UserModel.query.get(session["user_id"])
        if not user or user.role != "admin":
            flash("Solo administradores pueden acceder.", "danger")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated


@app.before_request
def load_user():
    g.user = UserModel.query.get(session["user_id"]) if "user_id" in session else None


@app.context_processor
def inject_user():
    return dict(current_user=g.user, enumerate=enumerate)


@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("index"))
    error = None
    if request.method == "POST":
        u = UserModel.query.filter_by(username=request.form["username"]).first()
        if u and check_password_hash(u.password, request.form["password"]):
            session["user_id"] = u.id
            flash(f"Bienvenido, {u.username}!", "success")
            return redirect(url_for("index"))
        error = "Usuario o contraseña incorrectos."
    return render_template("auth/login.html", error=error)


@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    flash("Sesión cerrada.", "success")
    return redirect(url_for("login"))


def get_today_revenue(today):
    paid_today = BillModel.query.filter(
        BillModel.paid == True,
        db.func.date(BillModel.paid_at) == today
    ).all()

    return sum(bill.total() for bill in paid_today)


def get_dashboard_data():
    today = datetime.now(timezone.utc).date()

    return {
        "total_products": ProductModel.query.filter_by(available=True).count(),
        "total_tables": TableModel.query.count(),
        "free_tables": TableModel.query.filter_by(occupied=False).count(),
        "open_orders": OrderModel.query.filter_by(status="open").count(),
        "pending_bills": BillModel.query.filter_by(paid=False).count(),
        "revenue_today": get_today_revenue(today),
        "recent_orders": OrderModel.query.order_by(OrderModel.created_at.desc()).limit(5).all(),
        "all_tables": TableModel.query.order_by(TableModel.number).all(),
        "upcoming_reservations": ReservationModel.query.filter(
            ReservationModel.date >= today,
            ReservationModel.status != "cancelled"
        ).order_by(ReservationModel.date, ReservationModel.time).limit(5).all()
    }


@app.route("/", methods=["GET"])
@login_required
def index():
    dashboard_data = get_dashboard_data()
    return render_template("index.html", **dashboard_data)


@app.route("/products", methods=["GET"])
@login_required
def list_products():
    cat   = request.args.get("category", "")
    q     = request.args.get("q", "")
    query = ProductModel.query
    if cat:
        query = query.filter_by(category=cat)
    if q:
        query = query.filter(ProductModel.name.ilike(f"%{q}%"))
    products   = query.order_by(ProductModel.category, ProductModel.name).all()
    categories = [c[0] for c in db.session.query(ProductModel.category).distinct().all()]
    return render_template("products/list.html", products=products, categories=categories, cat=cat, q=q)


@app.route("/products/new", methods=["GET", "POST"])
@admin_required
def create_product():
    error = None
    if request.method == "POST":
        name        = request.form.get("name", "").strip()
        price_s     = request.form.get("price", "").strip()
        category    = request.form.get("category", "General").strip()
        description = request.form.get("description", "").strip()
        try:
            if not name: raise ValueError("El nombre no puede estar vacío.")
            price = float(price_s)
            if price <= 0: raise ValueError("El precio debe ser mayor a 0.")
            db.session.add(ProductModel(name=name, price=price, category=category, description=description))
            db.session.commit()
            flash(f"Producto '{name}' creado.", "success")
            return redirect(url_for("list_products"))
        except ValueError as e:
            error = str(e)
    categories = ["Pizzas", "Hamburguesas", "Bebidas", "Ensaladas", "Platos", "Postres", "Otros"]
    return render_template("products/create.html", error=error, categories=categories)


@app.route("/products/<int:pid>/edit", methods=["GET", "POST"])
@admin_required
def edit_product(pid):
    p = ProductModel.query.get_or_404(pid)
    error = None
    if request.method == "POST":
        try:
            name  = request.form.get("name", "").strip()
            price = float(request.form.get("price", 0))
            if not name: raise ValueError("El nombre no puede estar vacío.")
            if price <= 0: raise ValueError("El precio debe ser mayor a 0.")
            p.name        = name
            p.price       = price
            p.category    = request.form.get("category", "General")
            p.description = request.form.get("description", "").strip()
            p.available   = request.form.get("available") == "on"
            db.session.commit()
            flash("Producto actualizado.", "success")
            return redirect(url_for("list_products"))
        except ValueError as e:
            error = str(e)
    categories = ["Pizzas", "Hamburguesas", "Bebidas", "Ensaladas", "Platos", "Postres", "Otros"]
    return render_template("products/edit.html", product=p, error=error, categories=categories)


@app.route("/products/<int:pid>/delete", methods=["POST"])
@admin_required
def delete_product(pid):
    p = ProductModel.query.get_or_404(pid)
    p.available = False
    db.session.commit()
    flash(f"Producto '{p.name}' desactivado.", "success")
    return redirect(url_for("list_products"))


@app.route("/tables", methods=["GET"])
@login_required
def list_tables():
    tables = TableModel.query.order_by(TableModel.number).all()
    return render_template("tables/list.html", tables=tables)


@app.route("/tables/new", methods=["GET", "POST"])
@login_required
def create_table():
    error = None
    if request.method == "POST":
        try:
            number   = int(request.form.get("number", 0))
            capacity = int(request.form.get("capacity", 0))
            location = request.form.get("location", "").strip()
            if number <= 0: raise ValueError("Número de mesa inválido.")
            if capacity <= 0: raise ValueError("Capacidad debe ser mayor a 0.")
            if TableModel.query.filter_by(number=number).first():
                raise ValueError(f"La mesa {number} ya existe.")
            db.session.add(TableModel(number=number, capacity=capacity, location=location or None))
            db.session.commit()
            flash(f"Mesa {number} creada.", "success")
            return redirect(url_for("list_tables"))
        except ValueError as e:
            error = str(e)
    return render_template("tables/create.html", error=error)


@app.route("/tables/<int:number>/occupy", methods=["POST"])
@login_required
def occupy_table(number):
    t = TableModel.query.filter_by(number=number).first_or_404()
    if t.occupied:
        flash("La mesa ya está ocupada.", "warning")
    else:
        t.occupied = True
        db.session.commit()
        flash(f"Mesa {number} ocupada.", "success")
    return redirect(url_for("list_tables"))


@app.route("/tables/<int:number>/release", methods=["POST"])
@login_required
def release_table(number):
    t = TableModel.query.filter_by(number=number).first_or_404()
    t.occupied = False
    db.session.commit()
    flash(f"Mesa {number} liberada.", "success")
    return redirect(url_for("list_tables"))


@app.route("/orders", methods=["GET"])
@login_required
def list_orders():
    status = request.args.get("status", "")
    q = OrderModel.query
    if status:
        q = q.filter_by(status=status)
    orders = q.order_by(OrderModel.created_at.desc()).all()
    return render_template("orders/list.html", orders=orders, status=status)


def get_valid_quantity(value):
    try:
        quantity = int(value)
        if quantity > 0:
            return quantity
    except ValueError:
        return None
    return None


def add_items_to_order(order, product_ids, quantities, item_notes):
    added = 0

    for index, product_id in enumerate(product_ids):
        if index >= len(quantities):
            continue

        quantity = get_valid_quantity(quantities[index])

        if quantity is None:
            continue

        product = ProductModel.query.get(int(product_id))

        if not product:
            continue

        note = item_notes[index] if index < len(item_notes) else ""

        db.session.add(OrderItemModel(
            order_id=order.id,
            product_id=product.id,
            quantity=quantity,
            unit_price=product.price,
            notes=note.strip() or None
        ))

        added += 1

    return added


def occupy_table_if_selected(table_id):
    if not table_id:
        return

    table = TableModel.query.get(int(table_id))

    if table:
        table.occupied = True


@app.route("/orders/new", methods=["GET", "POST"])
@login_required
def create_order():
    error = None
    products = ProductModel.query.filter_by(available=True).order_by(ProductModel.category).all()
    tables = TableModel.query.order_by(TableModel.number).all()

    if request.method != "POST":
        return render_template(ORDER_CREATE_TEMPLATE, products=products, tables=tables, error=error)

    product_ids = request.form.getlist("product_id")
    quantities = request.form.getlist("quantity")
    item_notes = request.form.getlist("item_notes")
    table_id = request.form.get("table_id") or None
    notes = request.form.get("notes", "").strip()

    if not product_ids:
        error = "Selecciona al menos un producto."
        return render_template(ORDER_CREATE_TEMPLATE, products=products, tables=tables, error=error)

    order = OrderModel(table_id=int(table_id) if table_id else None, notes=notes or None)
    db.session.add(order)
    db.session.flush()

    added = add_items_to_order(order, product_ids, quantities, item_notes)

    if added == 0:
        db.session.rollback()
        error = "No se agregó ningún producto válido."
        return render_template(ORDER_CREATE_TEMPLATE, products=products, tables=tables, error=error)

    occupy_table_if_selected(table_id)
    db.session.commit()

    flash(f"Orden #{order.id} creada. Total: S/. {order.total():.2f}", "success")
    return redirect(url_for("order_detail", oid=order.id))


@app.route("/orders/<int:oid>", methods=["GET"])
@login_required
def order_detail(oid):
    order    = OrderModel.query.get_or_404(oid)
    products = ProductModel.query.filter_by(available=True).order_by(ProductModel.name).all()
    return render_template("orders/detail.html", order=order, products=products)


@app.route("/orders/<int:oid>/close", methods=["POST"])
@login_required
def close_order(oid):
    order = OrderModel.query.get_or_404(oid)
    order.status = "closed"
    db.session.commit()
    flash(f"Orden #{oid} cerrada.", "success")
    return redirect(url_for("order_detail", oid=oid))


@app.route("/orders/<int:oid>/add-item", methods=["POST"])
@login_required
def add_order_item(oid):
    order = OrderModel.query.get_or_404(oid)

    if order.status != "open":
        flash("No se puede modificar una orden cerrada.", "danger")
        return redirect(url_for("order_detail", oid=oid))

    try:
        product_id = int(request.form.get("product_id"))
        quantity = int(request.form.get("quantity", "1"))

        if quantity <= 0:
            raise ValueError("La cantidad debe ser mayor a 0.")

        product = ProductModel.query.get_or_404(product_id)
        existing = OrderItemModel.query.filter_by(order_id=oid, product_id=product.id).first()

        if existing:
            existing.quantity += quantity
        else:
            db.session.add(OrderItemModel(
                order_id=oid,
                product_id=product.id,
                quantity=quantity,
                unit_price=product.price
            ))

        db.session.commit()
        flash(f"{product.name} agregado a la orden.", "success")
    except (ValueError, TypeError) as e:
        flash(str(e), "danger")

    return redirect(url_for("order_detail", oid=oid))


@app.route("/orders/<int:oid>/remove-item/<int:iid>", methods=["POST"])
@login_required
def remove_order_item(oid, iid):
    item = OrderItemModel.query.get_or_404(iid)
    order = OrderModel.query.get_or_404(oid)
    if order.status != "open":
        flash("No se puede modificar una orden cerrada.", "danger")
        return redirect(url_for("order_detail", oid=oid))
    db.session.delete(item)
    db.session.commit()
    flash("Ítem eliminado.", "success")
    return redirect(url_for("order_detail", oid=oid))


@app.route("/bills", methods=["GET"])
@login_required
def list_bills():
    status = request.args.get("status", "")
    q = BillModel.query
    if status == "paid":    q = q.filter_by(paid=True)
    if status == "pending": q = q.filter_by(paid=False)
    bills = q.order_by(BillModel.created_at.desc()).all()
    return render_template("bills/list.html", bills=bills, status=status)


@app.route("/bills/generate/<int:oid>", methods=["POST"])
@login_required
def generate_bill(oid):
    order = OrderModel.query.get_or_404(oid)
    if order.is_empty():
        flash("La orden está vacía.", "danger")
        return redirect(url_for("list_orders"))
    existing = BillModel.query.filter_by(order_id=oid, paid=False).first()
    if existing:
        flash("Ya existe una cuenta pendiente para esta orden.", "warning")
        return redirect(url_for("bill_detail", bid=existing.id))
    bill = BillModel(order_id=oid)
    db.session.add(bill)
    order.status = "closed"
    db.session.commit()
    flash(f"Cuenta #{bill.id} generada. Total: S/. {bill.total():.2f}", "success")
    return redirect(url_for("bill_detail", bid=bill.id))


@app.route("/bills/<int:bid>", methods=["GET"])
@login_required
def bill_detail(bid):
    bill = BillModel.query.get_or_404(bid)
    return render_template("bills/detail.html", bill=bill)


@app.route("/bills/<int:bid>/discount", methods=["POST"])
@login_required
def apply_discount(bid):
    bill = BillModel.query.get_or_404(bid)
    if bill.paid:
        flash("No se puede modificar una cuenta pagada.", "danger")
        return redirect(url_for("bill_detail", bid=bid))
    try:
        pct = float(request.form.get("percentage", 0))
        if pct < 0 or pct > 50: raise ValueError("Descuento debe estar entre 0% y 50%.")
        bill.discount_percentage = pct
        db.session.commit()
        flash(f"Descuento de {pct}% aplicado.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("bill_detail", bid=bid))


@app.route("/bills/<int:bid>/tip", methods=["POST"])
@login_required
def add_tip(bid):
    bill = BillModel.query.get_or_404(bid)
    if bill.paid:
        flash("No se puede modificar una cuenta pagada.", "danger")
        return redirect(url_for("bill_detail", bid=bid))
    try:
        amount = float(request.form.get("amount", 0))
        if amount < 0: raise ValueError("La propina no puede ser negativa.")
        bill.tip = amount
        db.session.commit()
        flash(f"Propina de S/. {amount:.2f} agregada.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("bill_detail", bid=bid))


@app.route("/bills/<int:bid>/pay", methods=["POST"])
@login_required
def pay_bill(bid):
    bill = BillModel.query.get_or_404(bid)
    if bill.paid:
        flash("Esta cuenta ya fue pagada.", "warning")
        return redirect(url_for("bill_detail", bid=bid))
    method = request.form.get("payment_method", "efectivo")
    bill.paid           = True
    bill.paid_at        = datetime.now(timezone.utc)
    bill.payment_method = method
    if bill.order.table:
        bill.order.table.occupied = False
    db.session.commit()
    flash(f"Cuenta #{bid} pagada con {method}. Total: S/. {bill.total():.2f}", "success")
    return redirect(url_for("list_bills"))


@app.route("/reservations", methods=["GET"])
@login_required
def list_reservations():
    filter_date = request.args.get("date", "")
    filter_status = request.args.get("status", "")
    q = ReservationModel.query
    if filter_date:
        try:
            d = datetime.strptime(filter_date, DATE_FORMAT).date()
            q = q.filter_by(date=d)
        except ValueError:
            pass
    if filter_status:
        q = q.filter_by(status=filter_status)
    reservations = q.order_by(ReservationModel.date, ReservationModel.time).all()
    tables = TableModel.query.order_by(TableModel.number).all()
    return render_template("reservations/list.html",
        reservations=reservations, tables=tables,
        filter_date=filter_date, filter_status=filter_status)


def get_required_form_value(form, field_name, error_message):
    value = form.get(field_name, "").strip()

    if not value:
        raise ValueError(error_message)

    return value


def get_positive_integer(value, error_message):
    number = int(value)

    if number <= 0:
        raise ValueError(error_message)

    return number


def get_reservation_date(date_value):
    reservation_date = datetime.strptime(date_value, DATE_FORMAT).date()

    if reservation_date < date.today():
        raise ValueError("La fecha no puede ser en el pasado.")

    return reservation_date


def get_optional_table_id(form):
    table_id = form.get("table_id")

    if not table_id:
        return None

    return int(table_id)


def build_reservation_from_form(form):
    customer_name = get_required_form_value(
        form,
        "customer_name",
        "El nombre del cliente es obligatorio."
    )
    date_value = get_required_form_value(
        form,
        "date",
        "La fecha es obligatoria."
    )
    time_value = get_required_form_value(
        form,
        "time",
        "La hora es obligatoria."
    )
    guests = get_positive_integer(
        form.get("guests", "0"),
        "El número de comensales debe ser mayor a 0."
    )
    phone = form.get("customer_phone", "").strip()
    notes = form.get("notes", "").strip()

    return ReservationModel(
        customer_name=customer_name,
        customer_phone=phone or None,
        guests=guests,
        date=get_reservation_date(date_value),
        time=time_value,
        table_id=get_optional_table_id(form),
        notes=notes or None
    )


@app.route("/reservations/new", methods=["GET", "POST"])
@login_required
def create_reservation():
    error = None
    tables = TableModel.query.order_by(TableModel.number).all()

    if request.method == "POST":
        try:
            reservation = build_reservation_from_form(request.form)
            db.session.add(reservation)
            db.session.commit()
            flash(f"Reserva para '{reservation.customer_name}' creada.", "success")
            return redirect(url_for("list_reservations"))
        except ValueError as e:
            error = str(e)

    return render_template(RESERVATION_CREATE_TEMPLATE, error=error, tables=tables)


@app.route("/reservations/<int:rid>/confirm", methods=["POST"])
@login_required
def confirm_reservation(rid):
    r = ReservationModel.query.get_or_404(rid)
    r.status = "confirmed"
    db.session.commit()
    flash(f"Reserva de {r.customer_name} confirmada.", "success")
    return redirect(url_for("list_reservations"))


@app.route("/reservations/<int:rid>/cancel", methods=["POST"])
@login_required
def cancel_reservation(rid):
    r = ReservationModel.query.get_or_404(rid)
    r.status = "cancelled"
    db.session.commit()
    flash(f"Reserva de {r.customer_name} cancelada.", "success")
    return redirect(url_for("list_reservations"))


@app.route("/reservations/<int:rid>/delete", methods=["POST"])
@admin_required
def delete_reservation(rid):
    r = ReservationModel.query.get_or_404(rid)
    db.session.delete(r)
    db.session.commit()
    flash("Reserva eliminada.", "success")
    return redirect(url_for("list_reservations"))


def get_last_seven_days_revenue():
    days = []
    revenues = []

    for i in range(6, -1, -1):
        current_day = (datetime.now(timezone.utc) - timedelta(days=i)).date()
        paid_bills = BillModel.query.filter(
            BillModel.paid == True,
            db.func.date(BillModel.paid_at) == current_day
        ).all()

        days.append(current_day.strftime("%d/%m"))
        revenues.append(round(sum(bill.total() for bill in paid_bills), 2))

    return days, revenues


def get_max_ticket(bills):
    max_ticket = 0

    for bill in bills:
        total = bill.total()

        if total > max_ticket:
            max_ticket = total

    return max_ticket


@app.route("/reports", methods=["GET"])
@admin_required
def reports():
    from sqlalchemy import func

    days, revenues = get_last_seven_days_revenue()

    top_products = db.session.query(
        ProductModel.name,
        func.sum(OrderItemModel.quantity).label("total_qty"),
        func.sum(OrderItemModel.quantity * OrderItemModel.unit_price).label("total_revenue")
    ).join(OrderItemModel).group_by(ProductModel.id)\
     .order_by(db.text("total_qty DESC")).limit(8).all()

    payment_stats = db.session.query(
        BillModel.payment_method,
        func.count(BillModel.id).label("count"),
        func.sum(BillModel.tip).label("total")
    ).filter_by(paid=True).group_by(BillModel.payment_method).all()

    all_paid = BillModel.query.filter_by(paid=True).all()
    total_revenue = sum(bill.total() for bill in all_paid)
    total_orders = OrderModel.query.count()
    total_bills = len(all_paid)
    avg_ticket = total_revenue / total_bills if total_bills else 0
    max_ticket = get_max_ticket(all_paid)

    return render_template("reports/index.html",
        days=days, revenues=revenues,
        top_products=top_products,
        payment_stats=payment_stats,
        total_revenue=total_revenue,
        total_orders=total_orders,
        total_bills=total_bills,
        avg_ticket=avg_ticket,
        max_ticket=max_ticket)


@app.route("/admin/users", methods=["GET"])
@admin_required
def list_users():
    users = UserModel.query.all()
    return render_template("auth/users.html", users=users)


@app.route("/admin/users/new", methods=["GET", "POST"])
@admin_required
def create_user():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        role     = request.form.get("role", "staff")
        try:
            if not username: raise ValueError("El usuario no puede estar vacío.")
            if len(password) < 6: raise ValueError("La contraseña debe tener al menos 6 caracteres.")
            if UserModel.query.filter_by(username=username).first():
                raise ValueError("Ese nombre de usuario ya existe.")
            db.session.add(UserModel(username=username,
                password=generate_password_hash(password), role=role))
            db.session.commit()
            flash(f"Usuario '{username}' creado.", "success")
            return redirect(url_for("list_users"))
        except ValueError as e:
            error = str(e)
    return render_template("auth/create_user.html", error=error)


@app.route("/admin/users/<int:uid>/delete", methods=["POST"])
@admin_required
def delete_user(uid):
    u = UserModel.query.get_or_404(uid)
    if u.username == "admin":
        flash("No se puede eliminar el usuario admin.", "danger")
        return redirect(url_for("list_users"))
    db.session.delete(u)
    db.session.commit()
    flash(f"Usuario '{u.username}' eliminado.", "success")
    return redirect(url_for("list_users"))


if __name__ == "__main__":
    initialize_database()
    app.run(host="127.0.0.1", port=8083, debug=True)