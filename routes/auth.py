from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_conn

bp = Blueprint("auth", __name__)


@bp.route("/")
def index():
    if "username" in session:
        return redirect(url_for("dashboard.dashboard"))
    else:
        return redirect(url_for("auth.login"))


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        hashed_password = generate_password_hash(password)

        conn = get_conn()
        cur = conn.cursor()

        # check if user exists
        cur.execute("SELECT id FROM users WHERE username=%s", (username,))
        existing = cur.fetchone()

        if existing:
            conn.close()
            error = "Username already exists"
            return render_template("register.html", error=error)

        # insert new user
        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, hashed_password),
        )

        conn.commit()
        conn.close()

        session["username"] = username
        return redirect(url_for("dashboard.dashboard"))

    return render_template("register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            "SELECT id, password FROM users WHERE username=%s",
            (username,),
        )

        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["username"] = username
            return redirect(url_for("dashboard.dashboard"))
        else:
            error = "Invalid username or password"
            return render_template("login.html", error=error)

    return render_template("login.html")


@bp.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("auth.login"))