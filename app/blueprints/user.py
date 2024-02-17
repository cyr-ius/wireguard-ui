from flask import Blueprint, flash, g, render_template, request
from flask_security import (
    auth_required,
    current_user,
    permissions_required,
)

from ..forms.forms import frm_gravatar, frm_user_profile
from ..helpers.utils import email_to_gravatar_url
from ..helpers.wireguard import wireguard_state
from ..models import Setting, User, db, first_run

user_bp = Blueprint("user", __name__, template_folder="templates", url_prefix="/user")


@user_bp.before_request
def before_request():
    # Check wireguard service status
    g.wg = wireguard_state()

    # Check first run
    if first_run():
        flash(
            "Please create endpoint server in Global settings and generate key pair in Server section",
            "first_run",
        )

    # Check site is in maintenance mode
    if (
        Setting().get("maintenance")
        and current_user.is_authenticated
        and not current_user.has_role("admin")
    ):
        return render_template("maintenance.html")


@user_bp.route("/profile", methods=["GET", "POST"])
@auth_required()
def profile():
    form = frm_user_profile()
    if request.method == "GET":
        user = User.query.filter_by(username=current_user.username).first()
        form = frm_user_profile(obj=user)

    if form.validate_on_submit():
        user = User.query.filter_by(username=current_user.username).first()
        form.populate_obj(user)
        db.session.add(user)
        db.session.commit()

    return render_template("profile_user.html", form=form, gravatar=frm_gravatar())


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


@user_bp.route("/gravatar", methods=["POST"])
@auth_required()
@permissions_required("admin-write")
def gravatar():
    gravatar_url = {}
    gravatar = frm_gravatar()
    if gravatar.validate_on_submit():
        user = User.query.filter_by(username=current_user.username).first()
        gravatar_url = email_to_gravatar_url(user.email)

    return {"gravatar_url": gravatar_url}
