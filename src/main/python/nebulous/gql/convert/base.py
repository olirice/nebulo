from __future__ import annotations

from abc import ABC, abstractproperty
from functools import lru_cache
from typing import TYPE_CHECKING, Type

from graphql import GraphQLField

if TYPE_CHECKING:
    from nebulous.sql.table_base import TableBase


class TableToGraphQLField(ABC):

    _cache = {}

    @lru_cache()
    def __init__(self, sqla_model: Type[TableBase]):
        self.sqla_model = sqla_model

    @property
    def type(self) -> GraphQLField:
        # Check cache
        self._cache[self.type_name] = self._cache.get(self.type_name, self._type)
        return self._cache[self.type_name]

    @abstractproperty
    def _type(self) -> GraphQLField:
        raise NotImplementedError()

    @abstractproperty
    def type_name(self) -> str:
        raise NotImplementedError()

    def resolver(self, obj, info, **user_kwarg) -> TableBase:
        raise NotImplementedError()
