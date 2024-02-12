from flask import g
from flask_migrate import Migrate
from flask_security import SQLAlchemySessionUserDatastore

from .base import db
from .security_too import Role, User, WebAuthn
from .setting import GlobalSettings, Setting  # noqa
from .wireguard import Clients, Server  # noqa


def init_app(app):
    db.init_app(app)
    _migrate = Migrate(app, db)  # lgtm [py/unused-local-variable]

    app.user_datastore = SQLAlchemySessionUserDatastore(
        db.session, user_model=User, role_model=Role, webauthn_model=WebAuthn
    )


def is_first_run():
    if (
        db.metadata.tables.get("server") is not None
        or db.metadata.tables.get("global_settings") is not None
        or db.metadata.tables.get("clients") is not None
    ):
        settings = db.session.query(GlobalSettings).first()
        server = db.session.query(Server).first()
        if settings is None or server is None:
            return True
        g.first_run = server.address is None and settings.endpoint_address is None
        return g.first_run
    return False
