import traceback
from flask_mail import Message
from flask import current_app, render_template

from ..models import Setting, Clients

from ..utils import wireguard_build_client_config
from .. import mail


def send_account_configuration(id, user_email):
    try:
        client = Clients.query.get(id)
        client.config = wireguard_build_client_config(id)
        subject = "Welcome to {}".format(Setting().get("site_name"))
        msg = Message(subject=subject)
        msg.recipients = [user_email]
        msg.body = "Please access the following link verify your email address."
        msg.html = render_template("email/account_configuration.html", client=client)
        msg.attach("wg0.conf", "text/plain", client.config)

        msg.sender = "Wireguard UI Robot"
        mail.send(msg)

    except Exception as e:
        current_app.logger.error(
            "Cannot send account verification email. Error: {}".format(e)
        )
        current_app.logger.debug(traceback.format_exc())
