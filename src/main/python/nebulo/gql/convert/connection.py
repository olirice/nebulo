from __future__ import annotations

import typing
from functools import lru_cache

from nebulo.text_utils import snake_to_camel

from ..alias import Argument, ConnectionType, Field, Int, List, NonNull
from ..default_resolver import default_resolver
from .cursor import Cursor
from .page_info import PageInfo

if typing.TYPE_CHECKING:
    pass

__all__ = ["connection_factory", "connection_args_factory"]


@lru_cache()
def connection_factory(sqla_model):
    name = f"{snake_to_camel(sqla_model.__table__.name)}Connection"

    from .edge import edge_factory

    edge = edge_factory(sqla_model)

    def build_attrs():
        return {
            "edges": Field(NonNull(List(NonNull(edge))), resolver=default_resolver),
            "pageInfo": Field(NonNull(PageInfo), resolver=default_resolver),
            "totalCount": Field(NonNull(Int), resolver=default_resolver),
        }

    return_type = ConnectionType(name=name, fields=build_attrs, description="")
    return_type.sqla_model = sqla_model
    return return_type


def connection_args_factory(sqla_model):
    from .condition import condition_factory

    condition = condition_factory(sqla_model)

    return {
        "first": Argument(Int, description="", out_name=None),
        # "last": Argument(Int),
        # "before": Argument(Cursor),
        "after": Argument(Cursor),
        "condition": Argument(condition),
    }
