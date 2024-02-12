import ipaddress
from ipaddress import IPv4Network

import netifaces
from flask import Blueprint, jsonify, request
from flask_security import auth_required, permissions_accepted, permissions_required

from ..forms.forms import frm_client
from ..helpers.wireguard import (
    wireguard_build_server_config,
    wireguard_keypair,
    wireguard_service,
)
from ..models import Clients, Server, db
from ..services.email import send_account_configuration

api_bp = Blueprint("api", __name__, template_folder="templates", url_prefix="/api")


@api_bp.route("/keypair", methods=["POST"])
@auth_required()
def KeyPair():
    try:
        return {
            "status": True,
            "message": "Key pair generated",
            "data": wireguard_keypair(),
        }
    except Exception:
        return {"status": False, "message": "Error to generate key pair"}, 401


@api_bp.route("/machine-ips", methods=["GET"])
@auth_required()
@permissions_accepted("admin-read")
def MachineIPAddresses():
    """MachineIPAddresses handler to get local interface ip addresses"""
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
    return jsonify(machine_ip_addresses)


@api_bp.route("/suggest-client-ips", methods=["GET", "POST"])
@auth_required()
def SuggestIPAllocation():
    """SuggestIPAllocation handler to get the list of ip address for client"""
    subnet_server = Server.query.one().address
    hosts_list = list(ipaddress.ip_network(subnet_server).hosts())
    ip_server = hosts_list[0].exploded
    ip_clients = [ip_server]
    for client in Clients.query.all():
        ip_clients.extend(client.allocated_ips.split(","))

    for ip in list(IPv4Network(subnet_server).hosts()):
        if (ip_free := ip.exploded) not in ip_clients:
            return jsonify([ip_free])
    return []


@api_bp.route("/set-status", methods=["POST"])
@auth_required()
@permissions_required("admin-write", "admin-read")
def setClientStatus():
    """// SetClientStatus handler to enable / disable a client"""
    try:
        id = request.json["id"]
        client = Clients.query.get(id)
        client.enabled = request.json["status"]
        db.session.commit()
        return {"status": True, "message": "Set status successful"}
    except Exception:
        return {"status": False, "message": "Error set status"}, 401


@api_bp.route("/client/", methods=["GET", "POST"])
@api_bp.route("/client/<int:id>", methods=["GET", "DELETE", "PUT"])
@auth_required()
@permissions_required("admin-write", "admin-read")
def Client(id=None):
    message = "API usage incorrect."
    form = frm_client()
    if request.method == "POST" and form.validate_on_submit():
        keypair = wireguard_keypair()
        private_key = keypair["PrivateKey"]
        public_key = keypair["PublicKey"]
        client = Clients(
            name=request.json.get("name"),
            email=request.json.get("email"),
            private_key=private_key,
            public_key=public_key,
            preshared_key="",
            allocated_ips=request.json.get("allocated_ips"),
            allowed_ips=request.json.get("allowed_ips"),
            use_server_dns=request.json.get("use_server_dns"),
            enabled=request.json.get("enabled"),
        )
        return client.create_peer()

    if request.method == "DELETE" and id is not None:
        client = Clients.query.get(id)
        return client.delete_peer()

    if request.method == "GET":
        if id is None:
            clients = Clients.query.all()
            all = [client.serialize() for client in clients]
            return jsonify(all)
        else:
            client = Clients.query.get(id)
            return {"client": client.serialize()}

    if request.method == "PUT" and id is not None:
        client = Clients.query.get(id)
        form.populate_obj(client)
        return client.update_peer()

    if form.errors:
        message = []
        for k, v in form.errors.items():
            message.append(f"{k}: {v}")

    return {"status": False, "message": message}, 401


@api_bp.route("/wg", methods=["POST"])
@auth_required()
@permissions_required("admin-write", "admin-read")
def ServerConfig():
    """ApplyServerConfig handler to write config file and restart Wireguard server"""
    if status := request.json.get("service"):
        try:
            if status == "start":
                wireguard_service("start")
                return {"status": True, "message": "service started"}
            elif status == "stop":
                wireguard_service("stop")
                return {"status": True, "message": "service stopped"}
            elif status == "restart":
                wireguard_service("stop")
                wireguard_service("start")
                return {"status": True, "message": "service restarted"}
        except Exception as error:
            return {"status": False, "message": error.args[0]}, 401

    if request.json.get("config"):
        try:
            wireguard_build_server_config()
            return {"status": True, "message": "Applied config successful"}
        except Exception as error:
            return {"status": False, "message": error.args[0]}, 401

    return {"status": False, "message": "method not found"}, 401


@api_bp.route("/email-client", methods=["POST"])
@auth_required()
@permissions_required("admin-write", "admin-read")
def EmailClient():
    """// EmailClient handler to sent the configuration via email"""
    id = request.json["id"]
    email = request.json["email"]
    send_account_configuration(int(id), email)
    return {"status": True, "message": "Send mail successfull"}
