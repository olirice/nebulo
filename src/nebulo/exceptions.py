class NebuloException(Exception):
    """Base exception for nebulo package"""


class SQLParseError(NebuloException):
    """An entity could not be parsed"""
