from datetime import datetime

from flask import abort, current_app

from ..helpers.utils import Serializer
from .base import db


class Server(db.Model):
    __tablename__ = "server"
    address = db.Column(db.String, nullable=False, primary_key=True)
    listen_port = db.Column(db.Integer, nullable=False)
    private_key = db.Column(db.String, nullable=False)
    public_key = db.Column(db.String, nullable=False)
    postup = db.Column(db.String, nullable=True)
    postdown = db.Column(db.String, nullable=True)
    update_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return "<Server {0}r>".format(self.name)


class Clients(db.Model, Serializer):
    __tablename__ = "clients"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, onupdate=datetime.now)
    public_key = db.Column(db.String, nullable=False)
    private_key = db.Column(db.String, nullable=False)
    preshared_key = db.Column(db.String, nullable=False)
    allocated_ips = db.Column(db.String, nullable=False)
    allowed_ips = db.Column(db.String, nullable=False)
    use_server_dns = db.Column(db.Boolean, nullable=False)
    enabled = db.Column(db.Boolean, nullable=False)

    def __init__(
        self,
        name,
        email,
        public_key,
        private_key,
        preshared_key,
        allocated_ips,
        allowed_ips,
        use_server_dns=True,
        enabled=False,
    ) -> None:
        self.name = name
        self.email = email
        self.public_key = public_key
        self.private_key = private_key
        self.preshared_key = preshared_key
        self.allocated_ips = allocated_ips
        self.allowed_ips = allowed_ips
        self.use_server_dns = use_server_dns
        self.enabled = enabled
        self.updated_at = datetime.now()

    def __repr__(self):
        return "<Clients {0}r>".format(self.name)

    def create_peer(self) -> None:
        # check if username existed
        name = Clients.query.filter(Clients.name == self.name).first()
        if name:
            abort(422, "Username is already in use")
        # check if email existed
        mail = Clients.query.filter(Clients.email == self.email).first()
        if mail:
            abort(422, "Email address is already in use")

        # check allocated ips existed
        for client in Clients.query.all():
            if self.allocated_ips in client.allocated_ips:
                abort(422, "Ip address is already in use")

        db.session.add(self)
        db.session.commit()

    def update_peer(self) -> None:
        """Update local user."""
        # Sanity check - account name
        if self.name == "":
            abort(422, "No user name specified")

        # read user and check that it exists
        peer = Clients.query.filter(Clients.name == self.name).first()
        if not peer:
            abort(422, "User does not exist")

        # check if new email exists (only if changed)
        if peer.email != self.email:
            checkuser = Clients.query.filter(Clients.email == self.email).first()
            if checkuser:
                abort(422, "New email address is already in use")
        if peer.allocated_ips != self.allocated_ips:
            checkip = Clients.query.filter(
                Clients.allocated_ips == self.allocated_ips
            ).first()
            if checkip:
                abort(422, "New ip address is already in use")
        db.session.commit()

    def delete_peer(self) -> None:
        try:
            Clients.query.filter(Clients.name == self.name).delete()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            msg = f"Cannot delete user {self.name} from DB. DETAIL: {str(e)}"
            current_app.logger.error(msg)
            abort(422, msg)

    def serialize(self):
        return Serializer.serialize(self)
