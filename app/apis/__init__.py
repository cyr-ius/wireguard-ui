"""Wireguard Apis."""
from .base import api, bp
from .system import api as system
from .wg import api as wireguard


def init_app(app):
    """Init API."""
    api.add_namespace(wireguard, path="/wg")
    api.add_namespace(system, path="/system")
    app.register_blueprint(bp, url_prefix="/api/1")
