from flask import Blueprint, render_template, session, redirect, url_for
from decorators import login_required

bp = Blueprint("settings", __name__)


@bp.route('/settings')
@login_required
def user_settings():


    return render_template(
        "user_settings.html",
        username=session.get("username")
    )