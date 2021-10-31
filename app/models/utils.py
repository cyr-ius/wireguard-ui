from sqlalchemy.inspection import inspect


class Serializer(object):
    def serialize(self):
        return {c: getattr(self, c) for c in inspect(self).attrs.keys()}

    @staticmethod
    def serialize_list(lst):
        return [m.serialize() for m in lst]
