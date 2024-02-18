from flask import (
    Blueprint,
    Response,
    flash,
    g,
    render_template,
    session,
    stream_with_context,
)
from flask_login import current_user
from flask_security import auth_required, permissions_required

from ..forms.forms import (
    frm_edit_client,
    frm_email_client,
    frm_global_settings,
    frm_server_interface,
)
from ..helpers.wireguard import (
    WireguardError,
    wireguard_build_client_config,
    wireguard_state,
    wireguard_status,
)
from ..models import Clients, GlobalSettings, Server, Setting, db, first_run

main_bp = Blueprint("index", __name__, template_folder="templates", url_prefix="/")


@main_bp.before_request
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

@main_bp.route("/clients", methods=["GET"])
@auth_required()
@permissions_required("admin-write", "admin-read")
def clients():
    clients_list = Clients.query.all()
    for client in clients_list:
        config = wireguard_build_client_config(client.id)
        client.config = config

    return render_template(
        "clients.html",
        clients_list=clients_list,
        form_email=frm_email_client(),
        form_edit_client=frm_edit_client(),
    )


@main_bp.route("/settings", methods=["GET"])
@auth_required()
@permissions_required("admin-write", "admin-read")
def settings():
    data = db.session.query(GlobalSettings).first()
    form = frm_global_settings(obj=data) if data else frm_global_settings()
    return render_template("settings.html", form=form)


@main_bp.route("/server", methods=["GET"])
@auth_required()
@permissions_required("admin-write", "admin-read")
def server():
    data = db.session.query(Server).first()
    form = frm_server_interface(obj=data) if data else frm_server_interface()
    return render_template("server.html", form=form)


@main_bp.route("/", methods=["GET"])
@auth_required()
def status():
    try:
        status = wireguard_status()
        peers = []
        for client in Clients.query.all():
            peer = {
                "idx": client.id,
                "name": client.name,
                "email": client.email,
                "public_key": client.public_key,
                "connected": status.get(client.public_key, {}).get("connected", False),
                "received_bytes": status.get(client.public_key, {}).get(
                    "received_bytes", ""
                ),
                "transmit_bytes": status.get(client.public_key, {}).get(
                    "transmit_bytes", ""
                ),
                "last_handshake_time": status.get(client.public_key, {}).get(
                    "latest handshake", ""
                ),
            }
            peers.append(peer)
    except WireguardError as error:
        return render_template("status.html", error=error)

    return render_template("status.html", peers=peers)


@main_bp.route("/download/<int:id>", methods=["GET"])
@auth_required()
@permissions_required("admin-write", "admin-read")
def download(id):
    strConfig = wireguard_build_client_config(id)

    return Response(stream_with_context(strConfig), mimetype="text/plain")
