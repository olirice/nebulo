"""
A base class to derive sql tables from
"""


from sqlalchemy import MetaData
from sqlalchemy.ext.automap import automap_base


class Table:
    """Base class for application sql tables that will contain mixins"""

    __abstract__ = True


Meta = MetaData()

TableBase = automap_base(metadata=Meta, cls=Table)
