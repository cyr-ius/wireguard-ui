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

def first_run():
    settings = db.session.query(GlobalSettings).first()
    server = db.session.query(Server).first()
    g.first_run = (settings is None or server is None) or (
        server.address is None and settings.endpoint_address is None
    )
    return g.first_run
