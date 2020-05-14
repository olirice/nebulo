from __future__ import annotations

from functools import lru_cache

from nebulo.config import Config
from nebulo.gql.alias import Argument, ConnectionType, Field, Int, List, NonNull
from nebulo.gql.convert.cursor import Cursor
from nebulo.gql.convert.page_info import PageInfo
from nebulo.gql.resolver.default import default_resolver
from sqlalchemy.ext.declarative import DeclarativeMeta

__all__ = ["connection_factory", "connection_args_factory"]


@lru_cache()
def connection_factory(sqla_model: DeclarativeMeta):
    from .edge import edge_factory

    name = Config.table_name_mapper(sqla_model) + "Connection"

    def build_attrs():
        edge = edge_factory(sqla_model)
        return {
            "edges": Field(NonNull(List(NonNull(edge))), resolve=default_resolver),
            "pageInfo": Field(NonNull(PageInfo), resolve=default_resolver),
            "totalCount": Field(NonNull(Int), resolve=default_resolver),
        }

    return_type = ConnectionType(name=name, fields=build_attrs, description="", sqla_model=sqla_model)
    return return_type


def connection_args_factory(sqla_model: DeclarativeMeta):
    from .condition import condition_factory

    condition = condition_factory(sqla_model)

    return {
        "first": Argument(Int, description="", out_name=None),
        "last": Argument(Int),
        "before": Argument(Cursor),
        "after": Argument(Cursor),
        "condition": Argument(condition),
    }
