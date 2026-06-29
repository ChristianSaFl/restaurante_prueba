import os
from datetime import datetime, date, timezone

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
DATE_FORMAT = "%Y-%m-%d"
RESERVATION_NOT_FOUND = "Reserva no encontrada."


class Reservation(db.Model):
    __tablename__ = "reservations"

    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(120), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=True)
    table_id = db.Column(db.Integer, nullable=True)
    guests = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), default="pending")
    notes = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


def reservation_to_dict(reservation):
    return {
        "id": reservation.id,
        "customer_name": reservation.customer_name,
        "customer_phone": reservation.customer_phone,
        "table_id": reservation.table_id,
        "guests": reservation.guests,
        "date": reservation.date.strftime(DATE_FORMAT),
        "time": reservation.time,
        "status": reservation.status,
        "notes": reservation.notes,
    }


def get_required_value(data, field_name, message):
    value = str(data.get(field_name, "")).strip()

    if not value:
        raise ValueError(message)

    return value


def get_positive_guests(value):
    try:
        guests = int(value)
    except ValueError:
        raise ValueError("El número de comensales debe ser válido.")

    if guests <= 0:
        raise ValueError("El número de comensales debe ser mayor a 0.")

    return guests


def get_valid_date(value):
    try:
        reservation_date = datetime.strptime(value, DATE_FORMAT).date()
    except ValueError:
        raise ValueError("La fecha debe tener formato YYYY-MM-DD.")

    if reservation_date < date.today():
        raise ValueError("La fecha no puede ser en el pasado.")

    return reservation_date


def get_optional_table_id(value):
    if value is None or value == "":
        return None

    try:
        return int(value)
    except ValueError:
        raise ValueError("La mesa debe ser válida.")


def build_reservation(data):
    customer_name = get_required_value(
        data,
        "customer_name",
        "El nombre del cliente es obligatorio."
    )
    date_value = get_required_value(
        data,
        "date",
        "La fecha es obligatoria."
    )
    time_value = get_required_value(
        data,
        "time",
        "La hora es obligatoria."
    )

    return Reservation(
        customer_name=customer_name,
        customer_phone=data.get("customer_phone"),
        table_id=get_optional_table_id(data.get("table_id")),
        guests=get_positive_guests(data.get("guests", "0")),
        date=get_valid_date(date_value),
        time=time_value,
        notes=data.get("notes"),
    )


def create_app(test_config=None):
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "RESERVATION_DATABASE_URL",
        "sqlite:///reservations_service.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "service": "reservations"}), 200

    @app.route("/api/reservations", methods=["GET"])
    def list_reservations():
        reservations = Reservation.query.order_by(
            Reservation.date,
            Reservation.time
        ).all()

        return jsonify([reservation_to_dict(r) for r in reservations]), 200

    @app.route("/api/reservations", methods=["POST"])
    def create_reservation():
        data = request.get_json() or {}

        try:
            reservation = build_reservation(data)
            db.session.add(reservation)
            db.session.commit()
            return jsonify(reservation_to_dict(reservation)), 201
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

    @app.route("/api/reservations/<int:reservation_id>/confirm", methods=["PUT"])
    def confirm_reservation(reservation_id):
        reservation = db.session.get(Reservation, reservation_id)

        if not reservation:
            return jsonify({"error": RESERVATION_NOT_FOUND}), 404

        reservation.status = "confirmed"
        db.session.commit()

        return jsonify(reservation_to_dict(reservation)), 200

    @app.route("/api/reservations/<int:reservation_id>/cancel", methods=["PUT"])
    def cancel_reservation(reservation_id):
        reservation = db.session.get(Reservation, reservation_id)

        if not reservation:
            return jsonify({"error": RESERVATION_NOT_FOUND}), 404

        reservation.status = "cancelled"
        db.session.commit()

        return jsonify(reservation_to_dict(reservation)), 200

    @app.route("/api/reservations/<int:reservation_id>", methods=["DELETE"])
    def delete_reservation(reservation_id):
        reservation = db.session.get(Reservation, reservation_id)

        if not reservation:
            return jsonify({"error": RESERVATION_NOT_FOUND}), 404

        db.session.delete(reservation)
        db.session.commit()

        return jsonify({"message": "Reserva eliminada."}), 200

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    service_app = create_app()
    service_app.run(host="127.0.0.1", port=5001, debug=True)