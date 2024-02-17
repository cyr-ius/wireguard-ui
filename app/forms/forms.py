from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, StringField, SubmitField
from wtforms.fields.simple import HiddenField
from wtforms.validators import DataRequired, Email, NumberRange, Optional
from wtforms.widgets import PasswordInput

from .validators import CIDRList, IPAddressList, IPNetwork, IPNetworkList
from .wtforms_button import ButtonField


class frm_server_interface(FlaskForm):
    address = StringField(
        "Server Interface Addresses",
        validators=[DataRequired(), IPNetwork()],
        render_kw={"data-role": "tagsinput"},
        default="192.168.1.0/24",
    )
    listen_port = IntegerField(
        "Listen Port",
        validators=[
            NumberRange(min=1, max=65535, message="Port must be in range 1..65535"),
            DataRequired(),
        ],
        default=51820,
    )
    private_key = StringField(
        "Private Key",
        validators=[DataRequired()],
        render_kw={"data-role": "tagsinput"},
        widget=PasswordInput(hide_value=False),
    )
    public_key = StringField("Public Key", validators=[DataRequired()])
    postup = StringField(
        "Post Up Script",
        validators=[DataRequired()],
        default="iptables -A FORWARD -i %i -j ACCEPT; iptables -A FORWARD -o %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE",
    )
    postdown = StringField(
        "Post Down Script",
        validators=[DataRequired()],
        default="iptables -D FORWARD -i %i -j ACCEPT; iptables -D FORWARD -o %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE",
    )
    submit = SubmitField("Save")


class frm_email_client(FlaskForm):
    email = StringField(
        "Email",
        validators=[Email(message="Not a valid email address."), DataRequired()],
    )
    client_id = HiddenField()
    submit = SubmitField("Send")


class frm_client(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField(
        "Email",
        validators=[Email(message="Not a valid email address."), DataRequired()],
    )
    allocated_ips = StringField(
        "IP Allocation", validators=[DataRequired(), CIDRList(is_ipaddress=True)]
    )
    allowed_ips = StringField(
        "Allowed IPs", validators=[DataRequired(), IPNetworkList()], default="0.0.0.0/0"
    )
    use_server_dns = BooleanField(
        "Use server DNS", validators=[Optional()], default="checked"
    )
    enabled = BooleanField(
        "Enable this client", validators=[Optional()], default="checked"
    )
    submit = SubmitField("Save")


class frm_edit_client(frm_client):
    client_id = HiddenField()


class frm_global_settings(FlaskForm):
    endpoint_address = StringField(
        "Endpoint Address",
        validators=[DataRequired("Please input your endpoint")],
        render_kw={"placeholder": "Endpoint Address"},
    )
    dns_servers = StringField(
        "DNS Servers",
        validators=[Optional(), IPAddressList()],
        render_kw={"placeholder": "Endpoint Address"},
    )
    mtu = IntegerField("MTU", validators=[Optional()], render_kw={"placeholder": "MTU"})
    persistent_keepalive = IntegerField(
        "Persistent Keepalive",
        validators=[Optional()],
        render_kw={"placeholder": "Persistent Keepalive"},
    )
    config_file_path = StringField(
        "Wireguard Config File Path",
        render_kw={"placeholder": "/etc/wireguard/wg0.conf"},
        default="/etc/wireguard/wg0.conf",
    )
    submit = SubmitField("Save")


class frm_user_profile(FlaskForm):
    first_name = StringField(
        "First name",
        validators=[DataRequired(message="Please input your first name")],
        render_kw={"placeholder": "First Name"},
    )
    last_name = StringField(
        "Last name",
        validators=[Optional()],
        render_kw={"placeholder": "Last Name"},
    )
    email = StringField(
        "Email",
        validators=[Email(message="Not a valid email address."), DataRequired()],
        render_kw={"placeholder": "Email"},
    )
    gravatar_url = StringField(
        "Gravatar url",
        validators=[Optional()],
        render_kw={"placeholder": "URI"},
    )
    submit = SubmitField("Save")


class frm_gravatar(FlaskForm):
    generate = ButtonField("Generate")
