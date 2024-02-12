from flask_security.models.fsqla_v3 import (
    FsModels,
    FsRoleMixin,
    FsUserMixin,
    FsWebAuthnMixin,
)

from .base import db

FsModels.set_db_info(db)


class User(db.Model, FsUserMixin):
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    gravatar_url = db.Column(db.String(2048))


class Role(db.Model, FsRoleMixin):
    pass


class WebAuthn(db.Model, FsWebAuthnMixin):
    pass
