from __future__ import annotations

from abc import ABC, abstractproperty
from typing import TYPE_CHECKING, Type

from graphql import GraphQLField

if TYPE_CHECKING:
    from nebulous.sql.table_base import TableBase


class TableToGraphQLField(ABC):
    def __init__(self, sqla_model: Type[TableBase]):
        self.sqla_model = sqla_model

    @abstractproperty
    def type(self) -> GraphQLField:
        raise NotImplementedError()

    def resolver(self, obj, info, **user_kwarg) -> TableBase:
        raise NotImplementedError()
