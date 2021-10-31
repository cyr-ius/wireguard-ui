from datetime import datetime
from .. import db


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
