from __future__ import annotations

import typing
from abc import ABC, abstractproperty
from functools import lru_cache

from ..alias import Field, InputField, InputObjectType, List, NonNull, ResolveInfo

if typing.TYPE_CHECKING:
    from nebulous.sql.table_base import TableBase


class TableToGraphQLField(ABC):

    registry = {}

    _cache = {}

    @lru_cache()
    def __init__(self, sqla_model: typing.Type[TableBase]):
        self.sqla_model = sqla_model
        self.registry[self.type_name] = self

    @property
    def type(self):
        # Check cache
        self._cache[self.type_name] = self._cache.get(self.type_name, self._type)
        return self._cache[self.type_name]

    @abstractproperty
    def _type(self):
        raise NotImplementedError()

    @abstractproperty
    def type_name(self) -> str:
        raise NotImplementedError()

    @property
    def arguments(self) -> typing.Dict[str, typing.Union[InputField, InputObjectType]]:
        return {}

    @abstractproperty
    def _resolver(self, obj, info: ResolveInfo, **kwargs) -> typing.Any:
        raise NotImplementedError()

    def resolver(self, obj, info: ResolveInfo, **kwargs) -> typing.Any:
        print(info.path)
        return self._resolver(obj, info, **kwargs)

    def field(
        self, nullable: bool = True, as_nullable_list: bool = False, as_nonnull_list: bool = False
    ):
        if as_nullable_list and as_nonnull_list:
            raise ValueError(
                "Only one of as_nullable_list and as_non_nullable_list may be provided"
            )

        _type = self.type if nullable else NonNull(self.type)

        if not as_nullable_list and not as_nonnull_list:
            return Field(_type, args=self.arguments, resolver=self.resolver)

        # Output type is a list
        _type = List(_type)

        if as_nonnull_list:
            _type = NonNull(_type)

        response = Field(_type, args=self.arguments, resolver=self.resolver)
        response.sqla_model = self.sqla_model
        return response
