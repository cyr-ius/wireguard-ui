"""Wireguard Apis."""
from flask import Blueprint
from flask_restx import Api

bp = Blueprint("api", __name__)
api = Api(
    app=bp,
    title="Wireguard API",
    version="1.0",
    description="API for Wireguard",
    doc="/doc",
    authorizations={
        "apikey": {"type": "apiKey", "in": "header", "name": "Authorization"}
    },
    security="apikey",
)
