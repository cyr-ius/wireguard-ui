from __future__ import annotations

import hashlib
import ipaddress
from datetime import date, datetime

from requests import get
from sqlalchemy.inspection import inspect


def show_all_attrs(value: str) -> list[str]:
    res = []
    for k in dir(value):
        res.append("%r %r\n" % (k, getattr(value, k)))
    return "\n".join(res)


def email_to_gravatar_url(email: str = "", size: int = 100) -> str:
    """AD doesn't necessarily have email."""
    email = "" if email is None else email
    hash_string = hashlib.md5(email.encode("utf-8")).hexdigest()
    return f"https://s.gravatar.com/avatar/{hash_string}?s={size}"


def public_ip_address() -> str:
    """Return public ip address."""
    ip = get("https://api.ipify.org").text
    return ip


def broadcast_address(network) -> str:
    """Return boradcast ip address."""
    obj = ipaddress.ip_network(network)
    return obj.broadcast


class Serializer(object):
    def serialize(self):
        return {c: self.serialize_date(getattr(self, c)) for c in inspect(self).attrs.keys()}

    @staticmethod
    def serialize_date(obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return obj
