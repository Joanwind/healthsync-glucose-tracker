from flask import Blueprint, render_template, request, redirect, url_for, session
from datetime import datetime
from db import get_conn
from decorators import login_required

bp = Blueprint("reminders", __name__)


@bp.route("/reminders")
@login_required
def reminders():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, med_name, remind_at, frequency, done
        FROM reminders
        WHERE username=%s
        ORDER BY done ASC, remind_at ASC
        """,
        (session["username"],)
    )
    rows = cur.fetchall()
    conn.close()

    reminders_list = []
    for r in rows:
        try:
            dt = datetime.fromisoformat(r["remind_at"])
            pretty = dt.strftime("%b %d, %Y · %I:%M %p")
        except Exception:
            pretty = r["remind_at"]

        reminders_list.append({
            "id": r["id"],
            "med_name": r["med_name"],
            "remind_at": r["remind_at"],
            "pretty_time": pretty,
            "frequency": r["frequency"],
            "done": r["done"]
        })

    pending = [x for x in reminders_list if x["done"] == 0]
    completed = [x for x in reminders_list if x["done"] == 1]

    return render_template("reminders.html", pending=pending, completed=completed)


@bp.route("/reminders/add", methods=["POST"])
def add_reminder():
    if "username" not in session:
        return redirect(url_for("auth.login"))

    med_name = request.form.get("med_name")
    remind_at = request.form.get("remind_at")
    frequency = request.form.get("frequency", "once")

    if not med_name or not remind_at:
        return redirect(url_for("reminders.reminders"))

    title = med_name

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO reminders (username, title, med_name, remind_at, frequency, done) VALUES (%s, %s, %s, %s, %s, 0)",
        (session["username"], title, med_name, remind_at, frequency)
    )
    conn.commit()
    conn.close()

    return redirect(url_for("reminders.reminders"))


@bp.route("/reminders/<int:rid>/toggle", methods=["POST"])
def toggle_reminder(rid):
    if "username" not in session:
        return redirect(url_for("auth.login"))

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT done FROM reminders WHERE id=%s AND username=%s",
        (rid, session["username"])
    )
    row = cur.fetchone()
    if not row:
        conn.close()
        return redirect(url_for("reminders.reminders"))

    new_done = 0 if row["done"] == 1 else 1
    cur.execute(
        "UPDATE reminders SET done=%s WHERE id=%s AND username=%s",
        (new_done, rid, session["username"])
    )

    conn.commit()
    conn.close()
    return redirect(url_for("reminders.reminders"))


@bp.route("/reminders/<int:rid>/delete", methods=["POST"])
@login_required
def delete_reminder(rid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM reminders WHERE id=%s AND username=%s",
        (rid, session["username"])
    )
    conn.commit()
    conn.close()

    return redirect(url_for("reminders.reminders"))


@bp.route("/reminders/<int:rid>/edit", methods=["GET", "POST"])
@login_required
def edit_reminder(rid):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, med_name, remind_at, frequency, done FROM reminders WHERE id=%s AND username=%s",
        (rid, session["username"])
    )
    reminder = cur.fetchone()

    if not reminder:
        conn.close()
        return redirect(url_for("reminders.reminders"))

    if request.method == "POST":
        med_name = request.form.get("med_name")
        remind_at = request.form.get("remind_at")
        frequency = request.form.get("frequency", "once")

        cur.execute(
            """
            UPDATE reminders
            SET med_name=%s, remind_at=%s, frequency=%s
            WHERE id=%s AND username=%s
            """,
            (med_name, remind_at, frequency, rid, session["username"])
        )
        conn.commit()
        conn.close()
        return redirect(url_for("reminders.reminders"))

    conn.close()
    return render_template("edit_reminder.html", reminder=reminder)