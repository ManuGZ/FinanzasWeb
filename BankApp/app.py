from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "mysql+pymysql://root:Luka123@127.0.0.1:3306/BankAPP"  # Remplazen donde dice contrasena con la que pusieron en wl workbench
app.config["SECRET_KEY"] = "BCDE123"
db = SQLAlchemy(app)


class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), unique=True, nullable=False)
    dni = db.Column(db.String(10), unique=True, nullable=False)
    edad = db.Column(db.Integer, nullable=False)
    telefono = db.Column(db.String(9), nullable=False)
    correo_electronico = db.Column(db.String(100), unique=True, nullable=False)
    contrasenia = db.Column(db.String(80), nullable=False)
    ingresos = db.Column(db.Float, nullable=False)


class Prestamo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    marca = db.Column(db.String(255), nullable=False)
    modelo = db.Column(db.String(255), nullable=False)
    anio = db.Column(db.Integer, nullable=False)
    monto_prestamo = db.Column(db.Float, nullable=False)
    pago_mensual = db.Column(db.Float, nullable=False)
    pago_total = db.Column(db.Float, nullable=False)
    tasa_interes = db.Column(db.Float, nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    pagos = db.relationship("Pago", backref="prestamo", lazy=True)


class Pago(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha_pago = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    monto = db.Column(db.Float, nullable=False)
    id_prestamo = db.Column(db.Integer, db.ForeignKey("prestamo.id"), nullable=False)


with app.app_context():
    db.create_all()


@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form["nombre"]
        dni = request.form["dni"]
        correo = request.form["correo"]
        telefono = request.form["telefono"]
        edad = request.form["edad"]
        contrasenia = request.form["contrasenia"]
        ingresos = request.form["ingresos"]
        nuevo_usuario = Usuario(
            nombre=nombre,
            dni=dni,
            edad=edad,
            telefono=telefono,
            correo_electronico=correo,
            contrasenia=contrasenia,
            ingresos=ingresos,
        )
        db.session.add(nuevo_usuario)
        db.session.commit()
        return redirect(url_for("inicio"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def inicio_sesion():
    if request.method == "POST":
        correo_electronico = request.form["correo"]
        contrasenia = request.form["contrasenia"]
        usuario = Usuario.query.filter_by(
            correo_electronico=correo_electronico, contrasenia=contrasenia
        ).first()
        if usuario:
            session["id_usuario"] = usuario.id
            return redirect(url_for("panel"))
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def cerrar_sesion():
    session.pop("id_usuario", None)
    return redirect(url_for("inicio"))


@app.route("/panel", methods=["GET", "POST"])
def panel():
    if "id_usuario" not in session:
        return redirect(url_for("inicio_sesion"))

    id_usuario = session["id_usuario"]
    if request.method == "POST":
        marca = request.form["marca"]
        modelo = request.form["modelo"]
        anio = request.form["anio"]
        monto_prestamo = float(request.form["monto_prestamo"])
        tasa_interes = float(request.form["tasa_interes"])
        periodos = int(request.form["periodos"])

        if monto_prestamo <= 0 or tasa_interes < 0 or periodos <= 0:
            return redirect(url_for("panel"))

        tasa_interes_mensual = tasa_interes / 100 / 12
        pago_mensual = (
            monto_prestamo
            * (tasa_interes_mensual * (1 + tasa_interes_mensual) ** periodos)
            / ((1 + tasa_interes_mensual) ** periodos - 1)
        )
        pago_total = pago_mensual * periodos

        nuevo_prestamo = Prestamo(
            marca=marca,
            modelo=modelo,
            anio=anio,
            monto_prestamo=monto_prestamo,
            pago_mensual=pago_mensual,
            pago_total=pago_total,
            tasa_interes=tasa_interes,
            id_usuario=id_usuario,
        )
        db.session.add(nuevo_prestamo)
        db.session.commit()

    usuario = Usuario.query.get(id_usuario)
    prestamos = Prestamo.query.filter_by(id_usuario=id_usuario).all()
    return render_template("panel.html", usuario=usuario, prestamos=prestamos)


if __name__ == "__main__":
    app.run(debug=True)
