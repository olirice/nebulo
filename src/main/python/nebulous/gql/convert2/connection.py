from __future__ import annotations

import typing
from functools import lru_cache

from ..alias import (
    Argument,
    EnumType,
    EnumValue,
    Field,
    InputField,
    InputObjectType,
    Int,
    List,
    NonNull,
    ObjectType,
)
from ..casing import snake_to_camel
from .cursor import Cursor
from .page_info import PageInfo
from .total_count import TotalCount

if typing.TYPE_CHECKING:
    pass

__all__ = ["connection_factory"]


@lru_cache()
def connection_factory(sqla_model):
    name = f"{snake_to_camel(sqla_model.__table__.name)}Connection"

    from .table import table_factory
    from .edge import edge_factory

    table = table_factory(sqla_model)
    edge = edge_factory(sqla_model)

    def build_attrs():
        return {
            "nodes": Field(NonNull(List(table))),
            "edges": Field(NonNull(List(NonNull(edge)))),
            "pageInfo": Field(NonNull(PageInfo)),
            "totalCount": Field(NonNull(TotalCount)),
        }

    return_type = ObjectType(name=name, fields=build_attrs, description="")
    return_type.sqla_model = sqla_model
    return return_type


def connection_args_factory(sqla_model):
    from .condition import condition_factory

    condition = condition_factory(sqla_model)
    return {
        "first": Argument(Int, default_value=10, description="", out_name=None),
        "last": Argument(Int),
        "before": Argument(Cursor),
        "after": Argument(Cursor),
        "condition": Argument(condition),
    }
