from flask import Blueprint, flash, g, render_template, request
from flask_security import (
    auth_required,
    current_user,
    permissions_required,
)

from ..forms.forms import frm_user_profile
from ..helpers.wireguard import wireguard_state
from ..models import Setting, User, db, is_first_run

user_bp = Blueprint("user", __name__, template_folder="templates", url_prefix="/user")


@user_bp.before_request
def before_request():
    g.wg = wireguard_state()
    g.collapsed = request.cookies.get("sidebar-collapsed", False) == "true"

    # Check site is in maintenance mode
    maintenance = Setting().get("maintenance")
    if (
        maintenance
        and current_user.is_authenticated
        and not current_user.has_role("admin")
    ):
        return render_template("maintenance.html")

    if is_first_run():
        flash(
            "Please create endpoint server in Server section and generate key pair in Global settings",
            "first_run",
        )


@user_bp.route("/profile", methods=["GET", "POST"])
@auth_required()
def profile():
    form = frm_user_profile()
    if request.method == "GET":
        profile = User.query.filter_by(username=current_user.username).first()
        form = frm_user_profile(obj=profile)

    if form.validate_on_submit():
        user = User.query.filter_by(username=current_user.username).first()
        form.populate_obj(user)
        db.session.add(user)
        db.session.commit()

    return render_template("profile_user.html", form=form)


@user_bp.route("/advanced", methods=["GET", "POST"])
@auth_required()
@permissions_required("admin-write", "admin-read")
def advanced():
    if request.method == "POST":
        Setting().set_maintenance(request.form.get("maintenance") == "on")

    dict = {
        "maintenance": bool(Setting().get("maintenance")),
    }
    return render_template("profile_adv.html", **dict)
