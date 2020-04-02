from base64 import b64decode as _unbase64
from base64 import b64encode as _base64


def to_base64(string):
    return _base64(string.encode("utf-8")).decode("utf-8")


def from_base64(string):
    return _unbase64(string).decode("utf-8")
