import sys, os

from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from functools import wraps
from datetime import datetime, timedelta, date
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


def p(x, y, z, w, v):
    d = 0
    if w > 0:
        d = x * w / 100
    t = (x - d) * 0.18
    r = x - d + t + y
    if v == True:
        r = r * 1.10
    if v == False:
        r = r * 1.0
    total = r
    return total


def get_product_info(pid):
    p = ProductModel.query.get(pid)
    if p == None:
        return None
    name = p.name
    price = p.price
    cat = p.category
    avail = p.available
    all_products = ProductModel.query.filter_by(available=True).all()
    count = 0
    for prod in all_products:
        if prod.category == cat:
            count = count + 1
    result = {}
    result['id'] = pid
    result['name'] = name
    result['price'] = price
    result['category'] = cat
    result['available'] = avail
    result['count_in_category'] = count
    unused_var = "esto no se usa"
    return result


def calculate_revenue_stats(bills):
    total = 0
    count = 0
    max_val = 0
    min_val = 999999
    for b in bills:
        if b.paid == True:
            t = b.total()
            total = total + t
            count = count + 1
            if t > max_val:
                max_val = t
            if t < min_val:
                min_val = t
            if t > 100:
                if t > 200:
                    if t > 500:
                        pass
    if count == 0:
        min_val = 0
    avg = 0
    if count > 0:
        avg = total / count
    return {'total': total, 'count': count, 'avg': avg, 'max': max_val, 'min': min_val}


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


@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada.", "success")
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    total_products = ProductModel.query.filter_by(available=True).count()
    total_tables   = TableModel.query.count()
    free_tables    = TableModel.query.filter_by(occupied=False).count()
    open_orders    = OrderModel.query.filter_by(status="open").count()
    pending_bills  = BillModel.query.filter_by(paid=False).count()
    today = datetime.utcnow().date()
    paid_today     = BillModel.query.filter(BillModel.paid == True, db.func.date(BillModel.paid_at) == today).all()
    revenue_today  = sum(b.total() for b in paid_today)
    recent_orders  = OrderModel.query.order_by(OrderModel.created_at.desc()).limit(5).all()
    all_tables     = TableModel.query.order_by(TableModel.number).all()
    upcoming_reservations = ReservationModel.query.filter(
        ReservationModel.date >= today,
        ReservationModel.status != "cancelled"
    ).order_by(ReservationModel.date, ReservationModel.time).limit(5).all()
    return render_template("index.html",
        total_products=total_products, total_tables=total_tables,
        free_tables=free_tables, open_orders=open_orders,
        pending_bills=pending_bills, revenue_today=revenue_today,
        recent_orders=recent_orders, all_tables=all_tables,
        upcoming_reservations=upcoming_reservations)


@app.route("/products")
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


@app.route("/tables")
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


@app.route("/orders")
@login_required
def list_orders():
    status = request.args.get("status", "")
    q = OrderModel.query
    if status:
        q = q.filter_by(status=status)
    orders = q.order_by(OrderModel.created_at.desc()).all()
    return render_template("orders/list.html", orders=orders, status=status)


@app.route("/orders/new", methods=["GET", "POST"])
@login_required
def create_order():
    error    = None
    products = ProductModel.query.filter_by(available=True).order_by(ProductModel.category).all()
    tables   = TableModel.query.order_by(TableModel.number).all()
    if request.method == "POST":
        pids     = request.form.getlist("product_id")
        qtys     = request.form.getlist("quantity")
        table_id = request.form.get("table_id") or None
        notes    = request.form.get("notes", "").strip()
        if not pids:
            error = "Selecciona al menos un producto."
        else:
            order = OrderModel(table_id=int(table_id) if table_id else None, notes=notes or None)
            db.session.add(order)
            db.session.flush()
            added = 0
            item_notes = request.form.getlist("item_notes")
            for i, (pid, qty_s) in enumerate(zip(pids, qtys)):
                try:
                    qty = int(qty_s)
                    if qty <= 0: continue
                except:
                    continue
                prod = ProductModel.query.get(int(pid))
                if prod:
                    inote = item_notes[i] if i < len(item_notes) else ""
                    db.session.add(OrderItemModel(
                        order_id=order.id, product_id=prod.id,
                        quantity=qty, unit_price=prod.price,
                        notes=inote.strip() or None))
                    added += 1
            if added == 0:
                db.session.rollback()
                error = "No se agregó ningún producto válido."
            else:
                if table_id:
                    t = TableModel.query.get(int(table_id))
                    if t: t.occupied = True
                db.session.commit()
                flash(f"Orden #{order.id} creada. Total: S/. {order.total():.2f}", "success")
                return redirect(url_for("order_detail", oid=order.id))
    return render_template("orders/create.html", products=products, tables=tables, error=error)


@app.route("/orders/<int:oid>")
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
    pid = request.form.get("product_id")
    qty_s = request.form.get("quantity", "1")
    try:
        qty  = int(qty_s)
        prod = ProductModel.query.get_or_404(int(pid))
        existing = OrderItemModel.query.filter_by(order_id=oid, product_id=prod.id).first()
        if existing:
            existing.quantity += qty
        else:
            db.session.add(OrderItemModel(
                order_id=oid, product_id=prod.id,
                quantity=qty, unit_price=prod.price))
        db.session.commit()
        flash(f"{prod.name} agregado a la orden.", "success")
    except Exception as e:
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


@app.route("/bills")
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


@app.route("/bills/<int:bid>")
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
    bill.paid_at        = datetime.utcnow()
    bill.payment_method = method
    if bill.order.table:
        bill.order.table.occupied = False
    db.session.commit()
    flash(f"Cuenta #{bid} pagada con {method}. Total: S/. {bill.total():.2f}", "success")
    return redirect(url_for("list_bills"))


@app.route("/reservations")
@login_required
def list_reservations():
    filter_date = request.args.get("date", "")
    filter_status = request.args.get("status", "")
    q = ReservationModel.query
    if filter_date:
        try:
            d = datetime.strptime(filter_date, "%Y-%m-%d").date()
            q = q.filter_by(date=d)
        except:
            pass
    if filter_status:
        q = q.filter_by(status=filter_status)
    reservations = q.order_by(ReservationModel.date, ReservationModel.time).all()
    tables = TableModel.query.order_by(TableModel.number).all()
    return render_template("reservations/list.html",
        reservations=reservations, tables=tables,
        filter_date=filter_date, filter_status=filter_status)


@app.route("/reservations/new", methods=["GET", "POST"])
@login_required
def create_reservation():
    error  = None
    tables = TableModel.query.order_by(TableModel.number).all()
    if request.method == "POST":
        try:
            name     = request.form.get("customer_name", "").strip()
            phone    = request.form.get("customer_phone", "").strip()
            guests_s = request.form.get("guests", "0")
            date_s   = request.form.get("date", "")
            time_s   = request.form.get("time", "")
            table_id = request.form.get("table_id") or None
            notes    = request.form.get("notes", "").strip()
            if not name:   raise ValueError("El nombre del cliente es obligatorio.")
            if not date_s: raise ValueError("La fecha es obligatoria.")
            if not time_s: raise ValueError("La hora es obligatoria.")
            guests = int(guests_s)
            if guests <= 0: raise ValueError("El número de comensales debe ser mayor a 0.")
            res_date = datetime.strptime(date_s, "%Y-%m-%d").date()
            if res_date < date.today():
                raise ValueError("La fecha no puede ser en el pasado.")
            db.session.add(ReservationModel(
                customer_name=name, customer_phone=phone or None,
                guests=guests, date=res_date, time=time_s,
                table_id=int(table_id) if table_id else None,
                notes=notes or None))
            db.session.commit()
            flash(f"Reserva para '{name}' creada.", "success")
            return redirect(url_for("list_reservations"))
        except ValueError as e:
            error = str(e)
    return render_template("reservations/create.html", error=error, tables=tables)


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


@app.route("/reports")
@admin_required
def reports():
    days, revenues = [], []
    for i in range(6, -1, -1):
        d    = (datetime.utcnow() - timedelta(days=i)).date()
        paid = BillModel.query.filter(BillModel.paid == True, db.func.date(BillModel.paid_at) == d).all()
        days.append(d.strftime("%d/%m"))
        revenues.append(round(sum(b.total() for b in paid), 2))

    from sqlalchemy import func
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

    all_paid      = BillModel.query.filter_by(paid=True).all()
    total_revenue = sum(b.total() for b in all_paid)
    total_orders  = OrderModel.query.count()
    total_bills   = len(all_paid)
    avg_ticket    = (total_revenue / total_bills) if total_bills else 0

    max_ticket = 0
    for b in all_paid:
        if b.total() > max_ticket:
            max_ticket = b.total()

    return render_template("reports/index.html",
        days=days, revenues=revenues,
        top_products=top_products,
        payment_stats=payment_stats,
        total_revenue=total_revenue,
        total_orders=total_orders,
        total_bills=total_bills,
        avg_ticket=avg_ticket,
        max_ticket=max_ticket)


@app.route("/admin/users")
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
    app.run(host="0.0.0.0", port=8083, debug=True)