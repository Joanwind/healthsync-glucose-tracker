from datetime import datetime, timedelta
import csv
from io import StringIO
from flask import Blueprint, Response, request, redirect, url_for, session, jsonify, render_template
from db import get_conn
from utils import parse_yyyy_mm_dd
from decorators import login_required

bp = Blueprint("glucose", __name__)


@bp.route("/export/glucose")
@login_required
def export_glucose_csv():

    start = parse_yyyy_mm_dd(request.args.get("start", "").strip())
    end = parse_yyyy_mm_dd(request.args.get("end", "").strip())

    where_clause = "username=%s"
    params = [session["username"]]

    if start and end:
        where_clause += " AND LEFT(measured_at,10) >= %s AND LEFT(measured_at,10) <= %s"
        params.extend([start, end])
        filename = f"healthsync_glucose_{start}_to_{end}.csv"

    else:
        try:
            days = int(request.args.get("days", 7))
        except:
            days = 7

        days = max(1, min(days, 90))

        since_str = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        where_clause += " AND LEFT(measured_at,10) >= %s"
        params.append(since_str)

        filename = f"healthsync_glucose_last_{days}_days.csv"

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        f"""
        SELECT measured_at, value, note
        FROM glucose_logs
        WHERE {where_clause}
        ORDER BY measured_at ASC
        """,
        tuple(params),
    )

    rows = cur.fetchall()
    conn.close()

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(["measured_at", "value_mgdl", "note"])

    for r in rows:
        writer.writerow([r["measured_at"], r["value"], r["note"] or ""])

    csv_data = output.getvalue()
    output.close()

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@bp.route("/api/glucose")
def api_glucose():

    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    start = parse_yyyy_mm_dd(request.args.get("start", "").strip())
    end = parse_yyyy_mm_dd(request.args.get("end", "").strip())

    where_clause = "username=%s"
    params = [session["username"]]

    meta = {}

    if start and end:

        where_clause += " AND LEFT(measured_at,10) >= %s AND LEFT(measured_at,10) <= %s"

        params.extend([start, end])

        meta = {"start": start, "end": end}

    else:

        try:
            days = int(request.args.get("days", 7))
        except:
            days = 7

        days = max(1, min(days, 90))

        since_str = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        where_clause += " AND LEFT(measured_at,10) >= %s"

        params.append(since_str)

        meta = {"days": days}

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        f"""
        SELECT value, measured_at, note
        FROM glucose_logs
        WHERE {where_clause}
        ORDER BY measured_at DESC
        """,
        tuple(params),
    )

    rows = cur.fetchall()
    conn.close()

    data = [
        {"value": r["value"], "measured_at": r["measured_at"], "note": r["note"]}
        for r in rows
    ]

    return jsonify({**meta, "count": len(data), "data": data})


@bp.route("/api/glucose/stats")
def api_glucose_stats():

    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        days = int(request.args.get("days", 7))
    except:
        days = 7

    days = max(1, min(days, 90))

    since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            AVG(value) as avg,
            MIN(value) as minv,
            MAX(value) as maxv
        FROM glucose_logs
        WHERE username=%s
        AND LEFT(measured_at,10) >= %s
        """,
        (session["username"], since_date),
    )

    s = cur.fetchone()

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

    latest = cur.fetchone()

    conn.close()

    return jsonify(
        {
            "days": days,
            "latest": latest["value"] if latest else None,
            "latest_time": latest["measured_at"] if latest else None,
            "avg": round(s["avg"], 1) if s and s["avg"] is not None else None,
            "min": s["minv"] if s else None,
            "max": s["maxv"] if s else None,
        }
    )


@bp.route("/glucose", methods=["GET", "POST"])
@login_required
def glucose_log():

    error = None

    conn = get_conn()
    cur = conn.cursor()

    if request.method == "POST":

        value = request.form.get("value", "").strip()
        measured_at = request.form.get("measured_at", "").strip()
        note = request.form.get("note", "").strip()

        try:
            v = int(value)

            if v < 40 or v > 400:
                raise ValueError()

        except:
            error = "Glucose value must be between 40 and 400."
            v = None

        if not measured_at:
            error = "Measured time is required."

        if not error:

            cur.execute(
                """
                INSERT INTO glucose_logs (username, measured_at, value, note)
                VALUES (%s, %s, %s, %s)
                """,
                (session["username"], measured_at, v, note),
            )

            conn.commit()

    cur.execute(
        """
        SELECT id, measured_at, value, note
        FROM glucose_logs
        WHERE username=%s
        ORDER BY measured_at DESC
        LIMIT 30
        """,
        (session["username"],),
    )

    rows = cur.fetchall()

    logs = []

    for r in rows:

        try:
            dt = datetime.fromisoformat(r["measured_at"])
            pretty = dt.strftime("%b %d, %Y · %I:%M %p")

        except Exception:
            pretty = r["measured_at"]

        flag = "ok"

        if r["value"] is not None:

            if r["value"] > 180:
                flag = "high"

            elif r["value"] < 70:
                flag = "low"

        logs.append(
            {
                "id": r["id"],
                "measured_at": r["measured_at"],
                "pretty_time": pretty,
                "value": r["value"],
                "note": r["note"],
                "flag": flag,
            }
        )

    since = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    cur.execute(
        """
        SELECT AVG(value) as avg7, MIN(value) as min7, MAX(value) as max7
        FROM glucose_logs
        WHERE username=%s
        AND LEFT(measured_at,10) >= %s
        """,
        (session["username"], since),
    )

    s = cur.fetchone()

    conn.close()

    stats = {
        "latest": logs[0]["value"] if logs else None,
        "avg7": round(s["avg7"]) if s and s["avg7"] is not None else None,
        "min7": s["min7"] if s else None,
        "max7": s["max7"] if s else None,
    }

    return render_template(
        "glucose_log.html",
        logs=logs,
        stats=stats,
        error=error,
    )


@bp.route("/glucose/<int:gid>/delete", methods=["POST"])
@login_required
def delete_glucose(gid):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM glucose_logs WHERE id=%s AND username=%s",
        (gid, session["username"]),
    )

    conn.commit()
    conn.close()

    return redirect(url_for("glucose.glucose_log"))