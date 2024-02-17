import os

basedir = os.path.abspath(os.path.abspath(os.path.dirname(__file__)))

# GENERAL SETTINGS
SITE_NAME = "Wireguard UI"
WUI_VERSION = "1.2"
GIT_URL = "https://api.github.com/repos/cyr-ius/wireguard-ui/releases/latest"

# ADMIN
FLASK_ADMIN_SWATCH = "cerulean"
FLASK_ADMIN_FLUID_LAYOUT = True

# BASIC APP CONFIG
SALT = os.getenv("SALT", None)
SECRET_KEY = os.getenv("SECRET_KEY", None)
FILESYSTEM_SESSIONS_ENABLED = os.getenv("FILESYSTEM_SESSIONS_ENABLED", True)

# DATABASE CONFIG
SQLA_DB_TYPE = os.getenv("SQLA_DB_TYPE", "sqlite")
SQLA_DB_USER = os.getenv("SQLA_DB_USER", None)
SQLA_DB_PASSWORD = os.getenv("SQLA_DB_PASSWORD", None)
SQLA_DB_HOST = os.getenv("SQLA_DB_HOST", None)
SQLA_DB_NAME = os.getenv("SQLA_DB_NAME", "wui")
SQLALCHEMY_TRACK_MODIFICATIONS = os.getenv("SQLALCHEMY_TRACK_MODIFICATIONS", True)

# DATABASE - MySQL
MARIADB_DATABASE_URI = (
    f"mysql://{SQLA_DB_USER}:{SQLA_DB_PASSWORD}@{SQLA_DB_HOST}/{SQLA_DB_NAME}"
)

# MAIL
MAIL_SERVER = os.getenv("MAIL_SERVER", None)
MAIL_PORT = os.getenv("MAIL_PORT", 25)
MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", False)
MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", False)
MAIL_USERNAME = os.getenv("MAIL_USERNAME", None)
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", None)
MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", None)
MAIL_MAX_EMAILS = os.getenv("MAIL_MAX_EMAILS", None)
MAIL_ASCII_ATTACHMENTS = os.getenv("MAIL_ASCII_ATTACHMENTS", False)

# SECURITY
SECURITY_PASSWORD_SALT = SALT
SECURITY_USERNAME_ENABLE = os.getenv("SECURITY_USERNAME_ENABLE", True)
SECURITY_CONFIRMABLE = os.getenv("SECURITY_CONFIRMABLE", False)
SECURITY_REGISTERABLE = os.getenv("SECURITY_REGISTERABLE", False)
SECURITY_RECOVERABLE = os.getenv("SECURITY_RECOVERABLE", True)
SECURITY_PASSWORD_LENGTH_MIN = os.getenv("SECURITY_PASSWORD_LENGTH_MIN", 10)
SECURITY_CHANGEABLE = os.getenv("SECURITY_CHANGEABLE", True)
SECURITY_EMAIL_SENDER = "no-reply@localhost"
SECURITY_TRACKABLE = os.getenv("SECURITY_TRACKABLE", True)
SECURITY_TWO_FACTOR = os.getenv("SECURITY_TWO_FACTOR", True)
SECURITY_TWO_FACTOR_ENABLED_METHODS = ["authenticator"]
SECURITY_TWO_FACTOR_AUTHENTICATOR_VALIDITY = 30
SECURITY_TWO_FACTOR_RESCUE_MAIL = SECURITY_EMAIL_SENDER
SECURITY_TOTP_SECRETS = {"1": SECRET_KEY}
SECURITY_TOTP_ISSUER = "Wireguard UI"
SECURITY_TWO_FACTOR_SETUP_TEMPLATE = "profile_authenticate.html"
SECURITY_CHANGE_PASSWORD_TEMPLATE = "profile_password.html"
SECURITY_JOIN_USER_ROLES = True
SECURITY_WEBAUTHN = True
SECURITY_WAN_REGISTER_TEMPLATE = "profile_wan_register.html"

# DEFAULT ACCOUNT
USERNAME = os.getenv("USERNAME", "admin")
PASSWORD = os.getenv("PASSWORD", "admin")
USER_MAIL = os.getenv("USER_MAIL", "please_change_me@localhost")

# WIREGUARD
WIREGUARD_STARTUP = os.getenv("WIREGUARD_STARTUP", True)

# IPTABLES DEFAULTS
POSTUP = "iptables -A FORWARD -i %i -j ACCEPT; iptables -A FORWARD -o %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE"
POSTDOWN = "iptables -D FORWARD -i %i -j ACCEPT; iptables -D FORWARD -o %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE"

# API Swagger documentation
SWAGGER_UI_DOC_EXPANSION = "list"
SWAGGER_UI_OPERATION_ID = True
SWAGGER_UI_REQUEST_DURATION = True
RESTX_MASK_SWAGGER = False
