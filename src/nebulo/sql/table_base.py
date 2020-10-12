"""
A base class to derive sql tables from
"""

from sqlalchemy import Table
from typing_extensions import Protocol, runtime_checkable


@runtime_checkable
class TableProtocol(Protocol):
    __table__: Table
