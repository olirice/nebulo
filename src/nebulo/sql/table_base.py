"""
A base class to derive sql tables from
"""


from sqlalchemy import MetaData, Table
from sqlalchemy.ext.automap import automap_base
from typing_extensions import Protocol, runtime_checkable


@runtime_checkable
class TableProtocol(Protocol):
    __table__: Table


Meta = MetaData()
TableBase = automap_base(metadata=Meta)
