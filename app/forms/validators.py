from wtforms.validators import ValidationError
import ipaddress


class CIDR(object):
    def __init__(self, message=None):
        if not message:
            message = "This format is not CIDR Address."
        self.message = message

    def __call__(self, form, field):
        try:
            ipaddress.ip_interface(field)
        except Exception:
            raise ValidationError(self.message)


class CIDR_IPAddress(object):
    """Check if CIDR is ip adress"""

    def __init__(self, message=None):
        if not message:
            message = "This format is not CIDR IP Address."
        self.message = message

    def __call__(self, form, field):
        try:
            interface = ipaddress.ip_interface(field.data)
            return interface.max_prefixlen == 32
        except Exception:
            return False


class CIDRList(object):
    def __init__(self, message=None, is_ipaddress=False):
        if not message:
            message = "This format is not CIDR Address List."
        self.message = message
        self.ip_address = is_ipaddress

    def __call__(self, form, field):
        datas = field.data.split(",")
        for data in datas:
            field.data = data
            try:
                if self.ip_address:
                    CIDR_IPAddress().__call__(None, field)
                else:
                    CIDR().__call__(None, field)
            except Exception:
                raise ValidationError(self.message)


class IPAddressList(object):
    def __init__(self, message=None):
        if not message:
            message = "IP address does not appear to be an IPv4 or IPv6 address."
        self.message = message

    def __call__(self, form, field):
        datas = field.data.split(",")
        for data in datas:
            try:
                ipaddress.ip_address(data)
            except Exception:
                raise ValidationError(self.message)


class IPNetwork(object):
    def __init__(self, message=None):
        if not message:
            message = "This format is not a subnet."
        self.message = message

    def __call__(self, form, field):
        try:

            try:
                ipaddress.ip_address(field.data)
                check = False
            except Exception:
                pass

            try:
                ipaddress.ip_interface(field.data)
                check = False
            except Exception:
                pass

            try:
                ipaddress.ip_network(field.data)
                check = True
            except Exception:
                pass

            if not check:
                raise ValidationError(self.message)
        except Exception:
            raise ValidationError(self.message)


class IPNetworkList(object):
    def __init__(self, message=None):
        if not message:
            message = "This format is not a subnet list."
        self.message = message

    def __call__(self, form, field):
        datas = field.data.split(",")
        for data in datas:
            field.data = data
            try:
                IPNetwork().__call__(None, field)
            except Exception:
                raise ValidationError(self.message)
