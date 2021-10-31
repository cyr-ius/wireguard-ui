from datetime import datetime

from flask import current_app

from .. import db
from .utils import Serializer


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
    ):
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

    def create_peer(self):
        # check if username existed
        name = Clients.query.filter(Clients.name == self.name).first()
        if name:
            return {"status": False, "message": "Username is already in use"}
        # check if email existed
        mail = Clients.query.filter(Clients.email == self.email).first()
        if mail:
            return {"status": False, "message": "Email address is already in use"}

        # check allocated ips existed
        for client in Clients.query.all():
            if self.allocated_ips in client.allocated_ips:
                return {"status": False, "message": "Ip address is already in use"}

        db.session.add(self)
        db.session.commit()
        return {"status": True, "message": "Created user successfully"}

    def update_peer(self):
        """Update local user."""
        # Sanity check - account name
        if self.name == "":
            return {"status": False, "message": "No user name specified"}

        # read user and check that it exists
        peer = Clients.query.filter(Clients.name == self.name).first()
        if not peer:
            return {"status": False, "message": "User does not exist"}

        # check if new email exists (only if changed)
        if peer.email != self.email:
            checkuser = Clients.query.filter(Clients.email == self.email).first()
            if checkuser:
                return {
                    "status": False,
                    "message": "New email address is already in use",
                }
        if peer.allocated_ips != self.allocated_ips:
            checkip = Clients.query.filter(
                Clients.allocated_ips == self.allocated_ips
            ).first()
            if checkip:
                return {"status": False, "message": "New ip address is already in use"}
        db.session.commit()
        return {"status": True, "message": "User updated successfully"}

    def delete_peer(self):
        try:
            Clients.query.filter(Clients.name == self.name).delete()
            db.session.commit()
            return {"status": True, "message": "Delete user successful"}
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                "Cannot delete user {0} from DB. DETAIL: {1}".format(self.name, e)
            )
            return {
                "status": True,
                "message": "Cannot delete user {0} from DB. DETAIL: {1}".format(
                    self.name, e
                ),
            }

    def serialize(self):
        return Serializer.serialize(self)
