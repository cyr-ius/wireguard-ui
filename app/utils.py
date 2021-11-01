import hashlib
import ipaddress
import re
import subprocess

import netifaces
from flask import current_app, g, render_template
from requests import get

from . import db
from .models import Clients, GlobalSettings, Server


def email_to_gravatar_url(email="", size=100):
    """
    AD doesn't necessarily have email
    """
    if email is None:
        email = ""

    hash_string = hashlib.md5(email.encode("utf-8")).hexdigest()
    return "https://s.gravatar.com/avatar/{0}?s={1}".format(hash_string, size)


def public_ip_address():
    ip = get("https://api.ipify.org").text
    return ip


def broadcast_address(network):
    obj = ipaddress.ip_network(network)
    return obj.broadcast


def is_first_run():
    if (
        db.session.bind.has_table("server")
        or db.session.bind.has_table("global_settings")
        or db.session.bind.has_table("clients")
    ):
        settings = db.session.query(GlobalSettings).first()
        server = db.session.query(Server).first()
        if settings is None or server is None:
            return True
        g.first_run = server.address is None and settings.endpoint_address is None
        return g.first_run
    return False


def wireguard_state(interface="wg0"):
    try:
        command = f"wg showconf {interface}"
        subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        return "started"
    except subprocess.CalledProcessError:
        return "stopped"


def wireguard_service(action, interface="wg0"):
    try:
        interfaces = netifaces.interfaces()
        if action == "stop":
            action = False
            if interface not in list(interfaces):
                current_app.logger.info("Service is already stopped")
                return action
            subprocess.check_output(
                f"wg-quick down {interface}",
                shell=True,
                stderr=subprocess.STDOUT,
                timeout=10,
            )
            current_app.logger.info("Service stop successful")
        elif action == "start":
            if wireguard_build_server_config() is None:
                raise WireguardError(
                    "Abort starting service because config server is not ready"
                )
            action = True
            if interface in list(interfaces):
                current_app.logger.info("Service is already started")
                return action
            subprocess.check_output(
                f"wg-quick up {interface}",
                shell=True,
                stderr=subprocess.STDOUT,
                timeout=10,
            )
            current_app.logger.info("Service start successful")
        return action
    except subprocess.CalledProcessError as error:
        raise WireguardError("Service failed (%s)" % error.output.decode().strip())


def wireguard_keypair():
    """Wireguard Key Pair handler to generate private and public keys"""
    try:
        PrivateKey = subprocess.check_output(["wg", "genkey"], stderr=subprocess.STDOUT)
        PrivateKey = PrivateKey.decode()[:-1]
        PublicKey = subprocess.check_output(
            f"echo {PrivateKey} | wg pubkey", shell=True, stderr=subprocess.STDOUT
        )
        PublicKey = PublicKey.decode()[:-1]
        return {"PrivateKey": PrivateKey, "PublicKey": PublicKey}
    except subprocess.CalledProcessError as error:
        raise WireguardError("Keypair %s" % error)


def wireguard_build_client_config(id):
    try:
        client = Clients.query.get(id)
        settings = GlobalSettings.query.first()
        server = Server.query.first()
        strConfig = render_template(
            "wg0_client.conf", client=client, settings=settings, server=server
        )
        return strConfig
    except Exception as error:
        raise WireguardError("Build client config %s" % error)


def wireguard_build_server_config():
    try:
        if (
            db.session.bind.has_table("server")
            or db.session.bind.has_table("global_settings")
            or db.session.bind.has_table("clients")
        ) is False:
            current_app.logger.warning("Please to set your server. Tables not found")
            return
        settings = db.session.query(GlobalSettings).first()
        server = db.session.query(Server).first()
        if server is None or settings is None:
            current_app.logger.warning("Please to set your server. Tables are empty")
            return
        server.address = list(ipaddress.ip_network(server.address).hosts())[0].exploded
        clients = db.session.query(Clients).all()
        template = current_app.jinja_env.get_template("wg0.conf")
        strConfig = template.render(clients=clients, settings=settings, server=server)
        with open(settings.config_file_path, "w") as f:
            f.write(strConfig)
        return strConfig
    except Exception as error:
        raise WireguardError("Build server config %s" % error) from error


def wireguard_status():
    popen = subprocess.Popen(["wg", "show"], stdout=subprocess.PIPE, encoding="utf8")
    items = {}
    section = {}
    section_name = None
    while True:
        line = popen.stdout.readline()
        arr = line.split(":")
        if len(arr) == 2:
            key = arr[0].strip()
            val = arr[1].strip()
            if key == "transfer":
                result = re.match(r"^(.*) (.*) received, (.*) (.*) sent$", val)
                section.update(
                    {"received_bytes": f"{result[1]} {result[2]}", "transmit_bytes": f"{result[3]} {result[4]}"}
                )
            if key == "latest handshake":
                section.update({"connected": True})
            if key in ["interface", "peer"]:
                if len(section) > 0:
                    items.update({section_name: section})
                    section = {}
                section_name = val
            section.update({key: val})

        if line == "" and popen.poll() is not None:
            if len(section) > 0:
                items.update({section_name: section})
            break

    returnStatus = popen.poll()
    if returnStatus != 0:
        raise WireguardError("Status not available [%s]" % returnStatus)
    return items


class WireguardError(Exception):
    def __init__(self, *args: object) -> None:
        if len(args) > 0:
            current_app.logger.error(args[0])
        super().__init__(*args)
