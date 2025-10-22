from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import mysql.connector
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import os
import psutil  # import para CPU e RAM
import time
from datetime import datetime

app = Flask(__name__)
app.secret_key = "chave_secreta_padrao"

# Removi a DLL porque vamos usar psutil no Python mesmo
monitor = None

# Conexão com o banco
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="senha",
            database="sistema_academico"
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao banco: {err}")
        return None

# Decorator para verificar login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("Faça login para acessar esta página.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# ===== ROTAS =====

@app.route("/", methods=["GET"])
def index():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")

        conn = get_db_connection()
        if not conn:
            flash("Erro de conexão com o banco de dados.", "error")
            return redirect(url_for("login"))

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user["password_hash"], senha):
            session["user"] = user["username"]
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Email ou senha incorretos.", "error")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if not username or not email or not password:
            flash("Preencha todos os campos.", "error")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)

        conn = get_db_connection()
        if not conn:
            flash("Erro de conexão com o banco de dados.", "error")
            return redirect(url_for("register"))

        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s,%s,%s)",
                (username, email, password_hash)
            )
            conn.commit()
            flash("Cadastro realizado com sucesso!", "success")
            return redirect(url_for("login"))
        except mysql.connector.IntegrityError:
            flash("Usuário ou e-mail já existe!", "error")
            return redirect(url_for("register"))
        finally:
            cursor.close()
            conn.close()

    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    session.pop("user", None)
    flash("Logout realizado.", "info")
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    start_time = time.time()
    
    # Pega uso CPU e RAM antes de renderizar
    cpu_before = psutil.cpu_percent(interval=None)
    ram_before = psutil.virtual_memory().percent

    response = render_template("dashboard.html", user=session.get("user"))

    cpu_after = psutil.cpu_percent(interval=None)
    ram_after = psutil.virtual_memory().percent

    elapsed = time.time() - start_time
    log_msg = (f"[{datetime.now()}] Tempo resposta: {elapsed:.3f}s | "
               f"CPU antes: {cpu_before}% | CPU depois: {cpu_after}% | "
               f"RAM antes: {ram_before}% | RAM depois: {ram_after}%\n")

    print(log_msg)
    with open("log.txt", "a") as f:
        f.write(log_msg)

    return response

@app.route("/status")
@login_required
def status():
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    return jsonify(cpu=cpu, ram=ram)

# Rotas restantes (alunos, turmas, aulas, atividades) permanecem iguais...

@app.route("/alunos", methods=["GET", "POST"])
@login_required
def alunos():
    conn = get_db_connection()
    if not conn:
        flash("Erro de conexão com o banco.", "error")
        return redirect(url_for("dashboard"))

    cursor = conn.cursor(dictionary=True)
    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        matricula = request.form.get("matricula")
        try:
            cursor.execute(
                "INSERT INTO alunos (nome, email, matricula) VALUES (%s, %s, %s)",
                (nome, email, matricula)
            )
            conn.commit()
            flash("Aluno cadastrado com sucesso!", "success")
        except mysql.connector.IntegrityError:
            flash("Matrícula já existe!", "error")
        except mysql.connector.Error as err:
            flash(f"Erro ao cadastrar aluno: {err}", "error")
            print(f"Erro ao inserir aluno: {err}")

    cursor.execute("SELECT * FROM alunos")
    alunos_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("alunos.html", alunos=alunos_list)

@app.route("/turmas", methods=["GET", "POST"])
@login_required
def turmas():
    conn = get_db_connection()
    if not conn:
        flash("Erro de conexão com o banco.", "error")
        return redirect(url_for("dashboard"))

    cursor = conn.cursor(dictionary=True)
    if request.method == "POST":
        nome = request.form.get("nome")
        descricao = request.form.get("descricao")
        try:
            cursor.execute(
                "INSERT INTO turmas (nome, descricao) VALUES (%s, %s)",
                (nome, descricao)
            )
            conn.commit()
            flash("Turma cadastrada com sucesso!", "success")
        except mysql.connector.Error as err:
            flash(f"Erro ao cadastrar turma: {err}", "error")
            print(f"Erro ao inserir turma: {err}")

    cursor.execute("SELECT * FROM turmas")
    turmas_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("turmas.html", turmas=turmas_list)

@app.route("/aulas", methods=["GET", "POST"])
@login_required
def aulas():
    conn = get_db_connection()
    if not conn:
        flash("Erro de conexão com o banco.", "error")
        return redirect(url_for("dashboard"))

    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM turmas")
    turmas_list = cursor.fetchall()

    if request.method == "POST":
        id_turma = request.form.get("id_turma")
        titulo = request.form.get("titulo")
        data_aula = request.form.get("data_aula")
        try:
            cursor.execute(
                "INSERT INTO aulas (id_turma, titulo, data_aula) VALUES (%s,%s,%s)",
                (id_turma, titulo, data_aula)
            )
            conn.commit()
            flash("Aula cadastrada com sucesso!", "success")
        except mysql.connector.Error as err:
            flash(f"Erro ao cadastrar aula: {err}", "error")
            print(f"Erro ao inserir aula: {err}")

    cursor.execute(
        "SELECT aulas.*, turmas.nome AS nome_turma FROM aulas JOIN turmas ON aulas.id_turma = turmas.id"
    )
    aulas_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("aulas.html", aulas=aulas_list, turmas=turmas_list)

@app.route("/atividades", methods=["GET", "POST"])
@login_required
def atividades():
    conn = get_db_connection()
    if not conn:
        flash("Erro de conexão com o banco.", "error")
        return redirect(url_for("dashboard"))

    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM aulas")
    aulas_list = cursor.fetchall()

    if request.method == "POST":
        id_aula = request.form.get("id_aula")
        titulo = request.form.get("titulo")
        descricao = request.form.get("descricao")
        data_entrega = request.form.get("data_entrega")
        try:
            cursor.execute(
                "INSERT INTO atividades (id_aula, titulo, descricao, data_entrega) VALUES (%s,%s,%s,%s)",
                (id_aula, titulo, descricao, data_entrega)
            )
            conn.commit()
            flash("Atividade cadastrada com sucesso!", "success")
        except mysql.connector.Error as err:
            flash(f"Erro ao cadastrar atividade: {err}", "error")
            print(f"Erro ao inserir atividade: {err}")

    cursor.execute(
        "SELECT atividades.*, aulas.titulo AS titulo_aula FROM atividades JOIN aulas ON atividades.id_aula = aulas.id"
    )
    atividades_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("atividades.html", atividades=atividades_list, aulas=aulas_list)


if __name__ == "__main__":
    app.run(debug=True)
