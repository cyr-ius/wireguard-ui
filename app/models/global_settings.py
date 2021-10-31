from datetime import datetime
from .. import db


class GlobalSettings(db.Model):
    __tablename__ = "global_settings"
    endpoint_address = db.Column(db.String, nullable=False, primary_key=True)
    dns_servers = db.Column(db.String, nullable=False)
    mtu = db.Column(db.Integer, nullable=True)
    persistent_keepalive = db.Column(db.Integer, nullable=True)
    config_file_path = db.Column(db.String, nullable=False, unique=True)
    updated_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return "<GlobalSettings {0}r>".format(self.name)
