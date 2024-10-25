
from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user
from flask_mysqldb import MySQL
from flask_sqlalchemy import SQLAlchemy
from flask import flash

app = Flask(__name__)
app.secret_key = 'samuel'

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "deportes_db"
app.config['MYSQL_UNIX_SOCKET'] = '/Applications/XAMPP/xamppfiles/var/mysql/mysql.sock'
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:@localhost/deportes_db?unix_socket=/Applications/XAMPP/xamppfiles/var/mysql/mysql.sock"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)

mysql = MySQL(app)

login_manager = LoginManager(app)

class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    def __init__(self, username, password):
        self.username = username
        self.password = password

class Jugador(db.Model):
    __tablename__= 'jugadores'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    apellido = db.Column(db.String(255), nullable=False)
    equipo_id = db.Column(db.Integer, db.ForeignKey('equipos.id'), nullable=False)
    equipo = db.relationship('Equipo', backref=db.backref('jugadores', lazy=True))
    posicion = db.Column(db.String(50), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)

class Equipo(db.Model):
    __tablename__='equipos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    liga = db.Column(db.String(50), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


#Ruta iniciar seción:
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        usuario = Usuario.query.filter_by(username=username, password=password).first()
        if usuario:
            login_user(usuario)
            return redirect(url_for("noticias"))
        return "Usuario o contraseña incorrectos"
    return render_template("login.html")

#Ruta para cerrar seción:
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("noticias"))



@app.route("/")
def index():
    return render_template("index.html")

@app.route("/noticias")
def noticias():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM noticias")
    noticias = cursor.fetchall()
    print(noticias)
    print("corrent_user")
    return render_template("noticias.html", noticias=noticias)

@app.route("/crear_noticia", methods=["POST"])
def crear_noticia():
    try: 
        titulo = request.form["titulo"]
        contenido = request.form["contenido"]
        fecha = request.form["fecha"]
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO noticias (titulo, contenido, fecha) VALUES(%s, %s, %s)", (titulo, contenido, fecha))
        mysql.connection.commit()
        print("Datos insertados con éxito")
        mensaje = "Noticia creada con éxito"
    except Exception as e:
        print("Error con la conexión de la base de datos:", str(e))
        mensaje = "Error al crear la noticia: " + str(e)
    return render_template("crear_noticia.html", mensaje=mensaje)

@app.route("/eliminar_noticia/<int:id>")
def eliminar_noticia(id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM noticias WHERE id = %s", (id,))
    mysql.connection.commit()
    return redirect(url_for("noticias"))

@app.route("/editar_noticia/<int:id>", methods=["GET", "POST"])
def editar_noticia(id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM noticias WHERE id = %s", (id,))
    noticia = cursor.fetchone()
    if request.method == "POST":
        titulo = request.form["titulo"]
        contenido = request.form["contenido"]       
        fecha = request.form["fecha"]
        cursor.execute("UPDATE noticias SET titulo = %s, contenido = %s, fecha = %s WHERE id = %s", (titulo, contenido, fecha, id))
        mysql.connection.commit()
        return redirect(url_for("noticias"))
    return render_template("editar_noticia.html", noticia=noticia)

@app.route("/crear_comentario/<int:noticia_id>", methods=["POST"])
def crear_comentario(noticia_id):
    usuario = request.form["usuario"]
    comentario = request.form["comentario"]
    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO comentarios (noticia_id, usuario, comentario, fecha) VALUES (%s, %s, %s, NOW())", (noticia_id, usuario, comentario))
    mysql.connection.commit()
    return redirect(url_for("noticias"))


@app.route("/obtener_comentarios/<int:noticia_id>")
def obtener_comentarios(noticia_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM comentarios WHERE noticia_id = %s", (noticia_id,))
    comentarios = cursor.fetchall()
    return render_template("comentarios.html", comentarios=comentarios)



#Rutas para equipos
@app.route("/agregar_equipo", methods=["GET", "POST"])
def agregar_equipo():
    if request.method == "POST":
        nombre = request.form["nombre"]
        liga = request.form["liga"]
        nuevo_equipo = Equipo(nombre=nombre, liga=liga)
        db.session.add(nuevo_equipo)
        db.session.commit()
        flash("Equipo agregado correctamente")
        return redirect(url_for("noticias"))
    return render_template("agregar_equipo.html")

@app.route('/equipos')
def mostrar_equipos():
    equipos = Equipo.query.all()
    print(equipos)#mesaje de depuración
    return render_template('equipos.html', equipos=equipos)



@app.route("/agregar_jugador", methods=["GET", "POST"])
def agregar_jugador():
    equipos = Equipo.query.all()  # Consulta a la base de datos para obtener todos los equipos
    if request.method == "POST":
        nombre = request.form.get("nombre")
        apellido = request.form.get("apellido")
        equipo_id = request.form.get("equipo_id")
        if not equipo_id:
            flash("Debe seleccionar un equipo")
            return redirect(url_for("agregar_jugador"))
        posicion = request.form.get("posicion")
        fecha_nacimiento = request.form.get("fecha_nacimiento")
        try:
            nuevo_jugador = Jugador(nombre=nombre, apellido=apellido, equipo_id=equipo_id, posicion=posicion, fecha_nacimiento=fecha_nacimiento)
            db.session.add(nuevo_jugador)
            db.session.commit()
            return redirect(url_for("noticias"))
        except Exception as e:
            flash("Error al agregar jugador: " + str(e))
            return redirect(url_for("agregar_jugador"))
    return render_template("agregar_jugador.html", equipos=equipos)






if __name__ == "__main__":
    app.run(debug=True)
