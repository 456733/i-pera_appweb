from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import mysql.connector

app = Flask(__name__)
app.secret_key = "ipera_secret_key"

# DECORADORES DE SEGURIDAD
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("Debes iniciar sesión para acceder.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "rol" not in session or session["rol"] != "admin":
            flash("Acceso denegado. Se requiere rol de Administrador.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# CONEXION A MYSQL
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1323",
    database="ipera_db"
)

cursor = db.cursor(dictionary=True)


# ===============================
# LOGIN
# ===============================

@app.route("/")
def login():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login_user():

    usuario= request.form["usuario"]
    password = request.form["password"]

    sql = "SELECT * FROM usuarios WHERE usuario=%s"
    cursor.execute(sql,(usuario,))

    user = cursor.fetchone()

    if user:
        # Validamos tanto la clave cifrada (hasheada) como una posible clave en texto plano heredada
        if check_password_hash(user["password"], password) or user["password"] == password:
            session["user"] = user["usuario"]
            session["rol"] = user["rol"]

            if user["rol"] == "admin":
                return redirect("/admin")
            else:
                return redirect("/vendedor")

    flash("Usuario o contraseña incorrectos", "error")
    return redirect(url_for("login"))


# ===============================
# LOGOUT
# ===============================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ===============================
# PANEL ADMIN
# ===============================

@app.route("/admin")
@admin_required
def admin():
    # Cargar lista de vendedores para mostrar eliminar_vendedor
    cursor.execute("SELECT * FROM usuarios WHERE rol='vendedor'")
    vendedores = cursor.fetchall()
    return render_template("admin_dashboard.html", vendedores=vendedores)


# ===============================
# PANEL VENDEDOR
# ===============================

@app.route("/vendedor")
@login_required
def vendedor():
    if session.get("rol") != "vendedor":
        return redirect("/")

    return render_template("vendedor_dashboard.html")


# ===============================
# INVENTARIO
# ===============================

@app.route("/inventario")
@login_required
def inventario():

    cursor.execute("SELECT * FROM celulares")
    celulares = cursor.fetchall()

    return render_template("inventario.html", celulares=celulares)


# ===============================
# AGREGAR CELULAR
# ===============================

@app.route("/agregar_celular", methods=["GET", "POST"])
@admin_required
def agregar_celular():
    if request.method == "GET":
        return render_template("agregar_celular.html")

    marca = request.form["marca"]
    modelo = request.form["modelo"]
    precio = request.form["precio"]
    stock = request.form["stock"]

    sql = """
    INSERT INTO celulares (marca,modelo,precio,stock)
    VALUES (%s,%s,%s,%s)
    """

    cursor.execute(sql,(marca,modelo,precio,stock))
    db.commit()
    flash("Celular agregado exitosamente.", "success")

    return redirect("/inventario")


# ===============================
# ELIMINAR CELULAR
# ===============================

@app.route("/eliminar_celular/<id>")
@admin_required
def eliminar_celular(id):

    sql = "DELETE FROM celulares WHERE id=%s"

    cursor.execute(sql,(id,))
    db.commit()
    flash("Celular eliminado del inventario.", "success")

    return redirect("/inventario")


# ===============================
# EDITAR CELULAR
# ===============================

@app.route("/editar_celular/<id>")
@admin_required
def editar_celular(id):

    sql = "SELECT * FROM celulares WHERE id=%s"

    cursor.execute(sql,(id,))
    celular = cursor.fetchone()

    return render_template("editar_celular.html", celular=celular)


@app.route("/actualizar_celular", methods=["POST"])
@admin_required
def actualizar_celular():

    id = request.form["id"]
    marca = request.form["marca"]
    modelo = request.form["modelo"]
    precio = request.form["precio"]
    stock = request.form["stock"]

    sql = """
    UPDATE celulares
    SET marca=%s, modelo=%s, precio=%s, stock=%s
    WHERE id=%s
    """

    cursor.execute(sql,(marca,modelo,precio,stock,id))
    db.commit()
    flash("Datos del celular actualizados correctamente.", "success")

    return redirect("/inventario")


# ===============================
# REGISTRAR VENDEDOR
# ===============================

@app.route("/registrar_vendedor", methods=["GET", "POST"])
@admin_required
def registrar_vendedor():
    if request.method == "GET":
        return render_template("registrar_vendedor.html")

    usuario = request.form["usuario"]
    password = request.form["password"]

    hashed_pwd = generate_password_hash(password)

    sql = """
    INSERT INTO usuarios (usuario,password,rol)
    VALUES (%s,%s,'vendedor')
    """

    cursor.execute(sql,(usuario,hashed_pwd))
    db.commit()
    flash("Vendedor registrado exitosamente.", "success")

    return redirect("/admin")


# ===============================
# ELIMINAR VENDEDOR
# ===============================

@app.route("/eliminar_vendedor/<id>")
@admin_required
def eliminar_vendedor(id):

    sql = "DELETE FROM usuarios WHERE id=%s AND rol='vendedor'"

    cursor.execute(sql,(id,))
    db.commit()
    flash("Vendedor eliminado correctamente.", "success")

    return redirect("/admin")


# ===============================
# REGISTRAR VENTA
# ===============================

@app.route("/registrar_venta", methods=["GET", "POST"])
@login_required
def registrar_venta():
    if request.method == "GET":
        cursor.execute("SELECT * FROM celulares WHERE stock > 0")
        celulares = cursor.fetchall()
        return render_template("registrar_venta.html", celulares=celulares)

    celular_id = request.form["celular_id"]
    precio = request.form["precio"]
    metodo_pago = request.form["metodo_pago"]

    # verificar inventario (Consistencia de Inventario RNF 06, R05)
    cursor.execute("SELECT stock FROM celulares WHERE id=%s",(celular_id,))
    celular = cursor.fetchone()

    if not celular or celular["stock"] <= 0:
        flash("Operación rechazada: No hay stock disponible de este producto.", "error")
        return redirect(url_for("registrar_venta"))

    # registrar venta
    sql = """
    INSERT INTO ventas (celular_id,precio,metodo_pago)
    VALUES (%s,%s,%s)
    """
    cursor.execute(sql,(celular_id,precio,metodo_pago))

    # actualizar inventario en tiempo real
    sql_update = """
    UPDATE celulares
    SET stock = stock - 1
    WHERE id=%s
    """
    cursor.execute(sql_update,(celular_id,))
    db.commit()
    
    flash("Venta registrada exitosamente.", "success")
    return redirect(url_for("ventas"))

# ===============================
@app.route("/ventas")
@login_required
def ventas():

    sql = """
    SELECT ventas.id, celulares.marca, celulares.modelo,
    ventas.precio, ventas.metodo_pago, ventas.fecha

    FROM ventas
    JOIN celulares ON ventas.celular_id = celulares.id
    """
    cursor.execute(sql)

    ventas = cursor.fetchall()

    return render_template("ventas.html", ventas=ventas)


# ===============================
# INICIAR APP
# ===============================

if __name__ == "__main__":
    app.run(debug=True)