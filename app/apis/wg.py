import datetime
import ipaddress
from ipaddress import IPv4Network

import netifaces
from flask_restx import Namespace, Resource, abort
from flask_security import auth_token_required, roles_required

from ..forms.forms import frm_client, frm_global_settings, frm_server_interface
from ..helpers.wireguard import (
    wireguard_build_server_config,
    wireguard_keypair,
    wireguard_service,
)
from ..models import Clients as tbl_clients
from ..models import GlobalSettings as tbl_settings
from ..models import Server as tbl_server
from ..models import db
from ..services.email import send_account_configuration
from .models import (
    client,
    forbidden,
    global_settings,
    ip_addresses,
    message,
    pairing_key,
    server,
    service,
    status,
    suggest_client_ip,
    version,
)

api = Namespace("wireguard", description="Wireguard API")

api.add_model("Error", message)
api.add_model("Forbidden", forbidden)
api.add_model("Client", client)
api.add_model("Version", version)
api.add_model("Server", server)
api.add_model("KeyPair", pairing_key)
api.add_model("IPaddresses", ip_addresses)
api.add_model("SuggestIP", suggest_client_ip)
api.add_model("ActiveStatus", status)
api.add_model("GlobalSettings", global_settings)
api.add_model("Service", service)


@api.response(422, "Error", message)
@api.route("/keypair")
class KeyPair(Resource):
    """Generate Keys for pairing."""

    @api.marshal_with(pairing_key)
    def get(self):
        try:
            return wireguard_keypair()
        except Exception:
            abort(422, "Error to generate key pair")


@api.response(403, "Forbidden", forbidden)
@api.route("/machine-ips")
class SuggestHostIPAddresses(Resource):
    """MachineIPAddresses handler to get local interface ip addresses"""

    @auth_token_required
    @roles_required("admin")
    @api.marshal_list_with(ip_addresses)
    def get(self):
        machine_ip_addresses = []
        interfaces = netifaces.interfaces()
        for interface in interfaces:
            ifa = netifaces.ifaddresses(interface)
            try:
                ip = ifa[netifaces.AF_INET][0].get("addr")
                machine_ip_addresses.append({"name": interface, "ip_address": ip})
            except Exception:
                pass
            try:
                ip = ifa[netifaces.AF_INET6][0].get("addr").split("%")[0]
                machine_ip_addresses.append({"name": interface, "ip_address": ip})
            except Exception:
                pass
        return machine_ip_addresses


@api.response(403, "Forbidden", forbidden)
@api.response(404, "SuggestNotFound", message)
@api.route("/suggest-client-ips")
class SuggestClientIPAddress(Resource):
    """Suggest IP Allocation handler to get the list of ip address for client"""

    @auth_token_required
    @roles_required("admin")
    @api.marshal_with(suggest_client_ip)
    def get(self):
        subnet_server = tbl_server.query.one().address
        hosts_list = list(ipaddress.ip_network(subnet_server).hosts())
        ip_server = hosts_list[0].exploded
        ip_clients = [ip_server]
        for client in tbl_clients.query.all():
            ip_clients.extend(client.allocated_ips.split(","))

        for ip in list(IPv4Network(subnet_server).hosts()):
            if (ip_free := ip.exploded) not in ip_clients:
                return {"ip_address": ip_free}
        abort(404, "Suggest ip not possible")


@api.response(204, "Success")
@api.response(403, "Forbidden", forbidden)
@api.response(404, "NotFound")
@api.response(422, "Error", message)
@api.route("/set-status/<int:id>")
class ClientStatus(Resource):
    """// SetClientStatus handler to enable / disable a client"""

    @auth_token_required
    @roles_required("admin")
    @api.expect(status)
    def post(self, id: int):
        try:
            if client := tbl_clients.query.get(id):
                client.enabled = api.payload["status"]
                db.session.commit()
                return "", 204
            abort(404, "Client id not found")
        except Exception as error:
            abort(422, str(error))


@api.response(403, "Forbidden", forbidden)
@api.response(404, "NotFound")
@api.response(422, "Error", message)
@api.route("/client/", endpoint="clients", methods=["GET", "POST"])
@api.route("/client/<int:id>", endpoint="client", methods=["GET", "DELETE", "PUT"])
class Client(Resource):
    """Client wireguard."""

    def __init__(self, id: int = None):
        self.form = frm_client()

    @roles_required("admin")
    @auth_token_required
    @api.expect(client, validate=False)
    @api.response(204, "Success")
    @api.response(422, "Error", message)
    def post(self):
        keypair = wireguard_keypair()
        private_key = keypair["PrivateKey"]
        public_key = keypair["PublicKey"]
        client = tbl_clients(
            name=api.payload.get("name"),
            email=api.payload.get("email"),
            private_key=private_key,
            public_key=public_key,
            preshared_key="",
            allocated_ips=api.payload.get("allocated_ips"),
            allowed_ips=api.payload.get("allowed_ips"),
            use_server_dns=api.payload.get("use_server_dns"),
            enabled=api.payload.get("enabled"),
        )
        if self.form.validate_on_submit():
            client.create_peer()
            return "", 204
        abort(422, "Incorrect data")

    @auth_token_required
    @roles_required("admin")
    def delete(self, id: int):
        if client := tbl_clients.query.get(id):
            client.delete_peer()
            return "", 204
        abort(404, "Client id not found")

    @auth_token_required
    @roles_required("admin")
    def get(self, id: int = None):
        if client := tbl_clients.query.get(id):
            return client.serialize()
        return [client.serialize() for client in tbl_clients.query.all()]

    @api.expect(client, validate=False)
    @auth_token_required
    @roles_required("admin")
    def put(self, id: int):
        if client := tbl_clients.query.get(id):
            self.form.populate_obj(client)
            client.update_peer()
            return "", 204
        abort(404, "Client id not found")


@api.response(204, "Success")
@api.response(403, "Forbidden", forbidden)
@api.response(422, "Error", message)
@api.route("/service")
class Service(Resource):
    """ApplyServerConfig handler to write config file and restart Wireguard server"""

    @auth_token_required
    @roles_required("admin")
    @api.expect(service)
    def post(self):
        try:
            match api.payload["state"]:
                case "start":
                    wireguard_service("start")
                    return "", 204
                case "stop":
                    wireguard_service("stop")
                    return "", 204
                case "restart":
                    wireguard_service("stop")
                    wireguard_service("start")
                    return "", 204
                case _:
                    raise Exception("Service not found")
        except Exception as error:
            return abort(422, str(error))


@api.response(204, "Success")
@api.response(403, "Forbidden", forbidden)
@api.response(422, "Error", message)
@api.route("/config")
class Config(Resource):
    """Apply server config handler to write config file."""

    @auth_token_required
    @roles_required("admin")
    def post(self):
        try:
            wireguard_build_server_config()
            return "", 204
        except Exception as error:
            abort(422, str(error))


@api.response(204, "Success")
@api.response(403, "Forbidden", forbidden)
@api.response(422, "Error", message)
@api.route("/email-client/<int:id>")
class SendEmail(Resource):
    """// EmailClient handler to sent the configuration via email"""

    @auth_token_required
    @roles_required("admin")
    def post(self, id: int):
        try:
            email = api.payload["email"]
            send_account_configuration(int(id), email)
            return "", 204
        except Exception as error:
            abort(422, str(error))


@api.response(204, "Success")
@api.response(403, "Forbidden", forbidden)
@api.response(422, "Error", message)
@api.route("/setting")
class Setting(Resource):
    """Apply server config handler to write config file."""

    @auth_token_required
    @roles_required("admin")
    @api.expect(global_settings)
    def post(self):
        try:
            form = frm_global_settings(**api.payload)
            if form.validate_on_submit():
                wggs = (
                    record
                    if (record := db.session.query(tbl_settings).first())
                    else tbl_settings()
                )
                form.populate_obj(wggs)
                wggs.updatedat = datetime.datetime.utcnow()
                db.session.commit()
            return "", 204
        except Exception as error:
            abort(422, str(error))


@api.response(204, "Success")
@api.response(403, "Forbidden", forbidden)
@api.response(422, "Error", message)
@api.route("/server")
class Server(Resource):
    """Apply server config handler to write config file."""

    @auth_token_required
    @roles_required("admin")
    @api.expect(server)
    def post(self):
        try:
            form = frm_server_interface(**api.payload)
            if form.validate_on_submit():
                wggs = (
                    record
                    if (record := db.session.query(tbl_server).first())
                    else tbl_server()
                )
                form.populate_obj(wggs)
                db.session.commit()
            return "", 204
        except Exception as error:
            abort(422, str(error))
