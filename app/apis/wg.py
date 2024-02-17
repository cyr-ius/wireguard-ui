import datetime
import ipaddress
from ipaddress import IPv4Network

import netifaces
import requests
from flask import current_app as ca
from flask_restx import Namespace, Resource, abort

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
    status,
    suggest_client_ip,
    version,
)

api = Namespace(
    "wireguard",
    description="Wireguard API",
    # decorators=[token_required, role_required("max")],
)

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


@api.response(422, "Error", message)
@api.response(403, "Forbidden", forbidden)
@api.route("/keypair")
# @auth_required()
class KeyPair(Resource):
    @api.marshal_with(pairing_key)
    def get(self):
        try:
            return wireguard_keypair()
        except Exception:
            abort(422, "Error to generate key pair")


@api.route("/machine-ips", endpoint="suggest_computer_ips")
# @auth_required()
# @permissions_accepted("admin-read")
class MachineIPAddresses(Resource):
    """MachineIPAddresses handler to get local interface ip addresses"""

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


@api.response(404, "SuggestNotFound", message)
@api.route("/suggest-client-ips")
# @auth_required()
class SuggestIPAllocation(Resource):
    """Suggest IP Allocation handler to get the list of ip address for client"""

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
@api.response(422, "Error", message)
@api.route("/set-status/<int:id>", endpoint="status")
# @auth_required()
# @permissions_required("admin-write", "admin-read")
class ClientStatus(Resource):
    """// SetClientStatus handler to enable / disable a client"""

    @api.expect(status)
    def post(self, id: int):
        try:
            client = tbl_clients.query.get(id)
            client.enabled = api.payload["status"]
            db.session.commit()
            return "", 204
        except Exception as error:
            abort(422, str(error))


@api.response(204, "Success")
@api.response(422, "Error", message)
@api.route("/client/", endpoint="clients", methods=["GET", "POST"])
@api.route("/client/<int:id>", endpoint="client", methods=["GET", "DELETE", "PUT"])
# @auth_required()
# @permissions_required("admin-write", "admin-read")
class Client(Resource):
    def __init__(self, id: int = None):
        self.form = frm_client()

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

    def delete(self, id: int):
        client = tbl_clients.query.get(id)
        client.delete_peer()
        return "", 204

    def get(self, id: int = None):
        if id:
            client = tbl_clients.query.get(id)
            return client.serialize()
        clients = tbl_clients.query.all()
        return [client.serialize() for client in clients]

    @api.expect(client)
    def put(self, id: int):
        client = tbl_clients.query.get(id)
        self.form.populate_obj(client)
        client.update_peer()
        return "", 204


@api.response(204, "Success")
@api.response(422, "Error", message)
@api.route("/service", endpoint="service")
# @auth_required()
# @permissions_required("admin-write", "admin-read")
class Service(Resource):
    """ApplyServerConfig handler to write config file and restart Wireguard server"""

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
@api.response(422, "Error", message)
@api.route("/config")
# @auth_required()
# @permissions_required("admin-write", "admin-read")
class Config(Resource):
    """Apply server config handler to write config file."""

    def post(self):
        try:
            wireguard_build_server_config()
            return "", 204
        except Exception as error:
            abort(422, str(error))


@api.response(204, "Success")
@api.response(422, "Error", message)
@api.route("/email-client/<int:id>", endpoint="email")
# @auth_required()
# @permissions_required("admin-write", "admin-read")
class EmailClient(Resource):
    """// EmailClient handler to sent the configuration via email"""

    def post(self, id: int):
        try:
            email = api.payload["email"]
            send_account_configuration(int(id), email)
            return "", 204
        except Exception as error:
            abort(422, str(error))


@api.response(422, "Error", message)
@api.route("/version")
# @auth_required()
# @permissions_required("admin-write", "admin-read")
class Version(Resource):
    @api.marshal_with(version)
    def get(self):
        try:
            response = requests.get(ca.config["GIT_URL"], timeout=ca.config["TIMEOUT"])
            response.raise_for_status()
            rjson = response.json()
            rjson["app_version"] = rjson.get("tag_name").replace("v", "")
            current_version = ca.config["VERSION"].replace("v", "")
            rjson.update(
                {
                    "current_version": current_version,
                    # "update_available": semver.compare(
                    #     rjson["app_version"], current_version
                    # ),
                }
            )
            return rjson
        except requests.RequestException as error:
            abort(422, str(error))


@api.response(204, "Success")
@api.response(422, "Error", message)
@api.route("/setting", endpoint="setting")
# @auth_required()
# @permissions_required("admin-write", "admin-read")
class Setting(Resource):
    """Apply server config handler to write config file."""

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
@api.response(422, "Error", message)
@api.route("/server")
# @auth_required()
# @permissions_required("admin-write", "admin-read")
class Server(Resource):
    """Apply server config handler to write config file."""

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
