from flask import Blueprint, render_template, session
from datetime import datetime, timedelta
from db import get_conn
from decorators import login_required

bp = Blueprint("dashboard", __name__)


@bp.route("/dashboard")
@login_required
def dashboard():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT value, measured_at
        FROM glucose_logs
        WHERE username=%s
        ORDER BY measured_at DESC
        LIMIT 1
        """,
        (session["username"],),
    )

    row = cur.fetchone()
    latest_value = row["value"] if row else None

    if latest_value is None:
        suggestion = "Add a glucose reading to start tracking trends."
    elif latest_value > 180:
        suggestion = "High glucose. Consider light activity and recheck in 15–30 minutes."
    elif latest_value < 70:
        suggestion = "Low glucose. Consider fast-acting carbs and recheck soon."
    else:
        suggestion = "Glucose within target range. Keep hydration and balanced meals."

    since_dt = datetime.now() - timedelta(days=7)
    since_str = since_dt.strftime("%Y-%m-%d")

    cur.execute(
        """
        SELECT measured_at, value
        FROM glucose_logs
        WHERE username=%s
        AND LEFT(measured_at, 10) >= %s
        ORDER BY measured_at ASC
        """,
        (session["username"], since_str),
    )

    rows = cur.fetchall()
    conn.close()

    dates = []
    values = []

    for r in rows:
        label = r["measured_at"][5:10]
        dates.append(label)
        values.append(r["value"])

    return render_template(
        "dashboard.html",
        latest_value=latest_value,
        suggestion=suggestion,
        dates=dates,
        values=values,
    )