from flask import Flask, render_template, request, redirect, session, url_for
import mysql.connector

app = Flask(__name__)
app.secret_key = "ipera_secret_key"


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

    sql = "SELECT * FROM usuarios WHERE usuario=%s AND password=%s"
    cursor.execute(sql,(usuario,password))

    user = cursor.fetchone()

    if user:

        session["user"] = user["usuario"]
        session["rol"] = user["rol"]

        if user["rol"] == "admin":
            return redirect("/admin")

        else:
            return redirect("/vendedor")

    return "Usuario o contraseña incorrectos"


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
def admin():

    if "rol" not in session or session["rol"] != "admin":
        return redirect("/")

    return render_template("admin_dashboard.html")


# ===============================
# PANEL VENDEDOR
# ===============================

@app.route("/vendedor")
def vendedor():

    if "rol" not in session or session["rol"] != "vendedor":
        return redirect("/")

    return render_template("vendedor_dashboard.html")


# ===============================
# INVENTARIO
# ===============================

@app.route("/inventario")
def inventario():

    cursor.execute("SELECT * FROM celulares")

    celulares = cursor.fetchall()

    return render_template("inventario.html", celulares=celulares)


# ===============================
# AGREGAR CELULAR
# ===============================

@app.route("/agregar_celular", methods=["POST"])
def agregar_celular():

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

    return redirect("/inventario")


# ===============================
# ELIMINAR CELULAR
# ===============================

@app.route("/eliminar_celular/<id>")
def eliminar_celular(id):

    sql = "DELETE FROM celulares WHERE id=%s"

    cursor.execute(sql,(id,))
    db.commit()

    return redirect("/inventario")


# ===============================
# EDITAR CELULAR
# ===============================

@app.route("/editar_celular/<id>")
def editar_celular(id):

    sql = "SELECT * FROM celulares WHERE id=%s"

    cursor.execute(sql,(id,))
    celular = cursor.fetchone()

    return render_template("editar_celular.html", celular=celular)


@app.route("/actualizar_celular", methods=["POST"])
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

    return redirect("/inventario")


# ===============================
# REGISTRAR VENDEDOR
# ===============================

@app.route("/registrar_vendedor", methods=["POST"])
def registrar_vendedor():

    usuario = request.form["usuario"]
    password = request.form["password"]

    sql = """
    INSERT INTO usuarios (usuario,password,rol)
    VALUES (%s,%s,'vendedor')
    """

    cursor.execute(sql,(usuario,password))
    db.commit()

    return redirect("/admin")


# ===============================
# ELIMINAR VENDEDOR
# ===============================

@app.route("/eliminar_vendedor/<id>")
def eliminar_vendedor(id):

    sql = "DELETE FROM usuarios WHERE id=%s AND rol='vendedor'"

    cursor.execute(sql,(id,))
    db.commit()

    return redirect("/admin")


# ===============================
# REGISTRAR VENTA
# ===============================

@app.route("/registrar_venta", methods=["POST"])
def registrar_venta():

    celular_id = request.form["celular_id"]
    precio = request.form["precio"]
    metodo_pago = request.form["metodo_pago"]

    # verificar inventario
    cursor.execute("SELECT stock FROM celulares WHERE id=%s",(celular_id,))
    celular = cursor.fetchone()

    if celular["stock"] <= 0:
        return "No hay stock disponible"

    # registrar venta
    sql = """
    INSERT INTO ventas (celular_id,precio,metodo_pago)
    VALUES (%s,%s,%s)
    """

    cursor.execute(sql,(celular_id,precio,metodo_pago))

    # actualizar inventario
    sql_update = """
    UPDATE celulares
    SET stock = stock - 1
    WHERE id=%s
    """

    cursor.execute(sql_update,(celular_id,))
    db.commit()

    return "Venta registrada correctamente"

# ===============================
# VER VENTAS
# ===============================

@app.route("/ventas")

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