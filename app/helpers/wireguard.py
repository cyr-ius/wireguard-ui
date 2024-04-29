"""Wireguard functions."""

from __future__ import annotations

import ipaddress
import re
import subprocess
from typing import Any, Text

import netifaces
from flask import current_app, render_template

from ..models import Clients, GlobalSettings, Server, db


def wireguard_state(interface: str = "wg0") -> str:
    try:
        command = f"wg showconf {interface}"
        subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        return "stopped"

    return "started"


def wireguard_service(action: str, interface: str = "wg0") -> None:
    try:
        interfaces = netifaces.interfaces()
        match action:
            case "stop":
                if interface not in list(interfaces):
                    current_app.logger.info("Service is already stopped")
                subprocess.check_output(
                    f"wg-quick down {interface}",
                    shell=True,
                    stderr=subprocess.STDOUT,
                    timeout=10,
                )
                current_app.logger.info("Service stop successful")
            case "start":
                if wireguard_build_server_config() is None:
                    raise WireguardError(
                        "Abort starting service because config server is not ready"
                    )
                if interface in list(interfaces):
                    current_app.logger.info("Service is already started")
                subprocess.check_output(
                    f"wg-quick up {interface}",
                    shell=True,
                    stderr=subprocess.STDOUT,
                    timeout=10,
                )
                current_app.logger.info("Service start successful")
    except subprocess.CalledProcessError as error:
        raise WireguardError("Service failed (%s)" % error.output.decode().strip())


def wireguard_keypair() -> dict[str, str]:
    """Wireguard Key Pair handler to generate private and public keys"""
    try:
        PrivateKey = subprocess.check_output(["wg", "genkey"], stderr=subprocess.STDOUT)
        PrivateKey = PrivateKey.decode()[:-1]
        PublicKey = subprocess.check_output(
            f"echo {PrivateKey} | wg pubkey", shell=True, stderr=subprocess.STDOUT
        )
        PublicKey = PublicKey.decode()[:-1]
    except subprocess.CalledProcessError as error:
        raise WireguardError("Keypair %s" % error)

    return {"PrivateKey": PrivateKey, "PublicKey": PublicKey}


def wireguard_build_client_config(id: int) -> Text:
    try:
        client = Clients.query.get(id)
        settings = GlobalSettings.query.first()
        server = Server.query.first()
    except Exception as error:
        raise WireguardError("Build client config %s" % error)

    return render_template(
        "wg0_client.conf", client=client, settings=settings, server=server
    )


def wireguard_build_server_config() -> Text | None:
    try:
        if (
            db.metadata.tables.get("server") is not None
            or db.metadata.tables.get("global_settings") is not None
            or db.metadata.tables.get("clients") is not None
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
    except Exception as error:
        raise WireguardError(
            "Error while building server configuration ({error})"
        ) from error
    return strConfig


def wireguard_status() -> dict[str, Any]:
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
                    {
                        "received_bytes": f"{result[1]} {result[2]}",
                        "transmit_bytes": f"{result[3]} {result[4]}",
                    }
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
