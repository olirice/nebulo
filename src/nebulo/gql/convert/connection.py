from __future__ import annotations

from functools import lru_cache

from nebulo.config import Config
from nebulo.gql.alias import Argument, ConnectionType, EdgeType, Field, InputObjectType, Int, List, NonNull
from nebulo.gql.convert.column import convert_column_to_input
from nebulo.gql.relay.cursor import Cursor
from nebulo.gql.relay.page_info import PageInfo
from nebulo.gql.resolve.resolvers.default import default_resolver
from nebulo.sql.inspect import get_columns
from nebulo.sql.table_base import TableProtocol

__all__ = ["connection_field_factory"]


@lru_cache()
def connection_field_factory(sqla_model: TableProtocol, resolver, not_null=False) -> Field:
    relevant_type_name = Config.table_type_name_mapper(sqla_model)
    connection = connection_factory(sqla_model)
    condition = condition_factory(sqla_model)
    args = {
        "first": Argument(Int, description="", out_name=None),
        "last": Argument(Int),
        "before": Argument(Cursor),
        "after": Argument(Cursor),
        "condition": Argument(condition),
    }
    return Field(
        NonNull(connection) if not_null else connection,
        args=args,
        resolve=resolver,
        description=f"Reads and enables pagination through a set of {relevant_type_name}",
    )


@lru_cache()
def edge_factory(sqla_model: TableProtocol) -> EdgeType:
    from .table import table_factory

    name = Config.table_type_name_mapper(sqla_model) + "Edge"

    def build_attrs():
        return {"cursor": Field(Cursor), "node": Field(table_factory(sqla_model))}

    edge = EdgeType(name=name, fields=build_attrs, description="", sqla_model=sqla_model)
    return edge


@lru_cache()
def condition_factory(sqla_model: TableProtocol) -> InputObjectType:
    result_name = f"{Config.table_name_mapper(sqla_model)}Condition"

    attrs = {}
    for column in get_columns(sqla_model):
        field_key = Config.column_name_mapper(column)
        attrs[field_key] = convert_column_to_input(column)
    return InputObjectType(result_name, attrs, description="")


@lru_cache()
def connection_factory(sqla_model: TableProtocol) -> ConnectionType:
    name = Config.table_type_name_mapper(sqla_model) + "Connection"

    def build_attrs():
        edge = edge_factory(sqla_model)
        return {
            "edges": Field(NonNull(List(NonNull(edge))), resolve=default_resolver),
            "pageInfo": Field(NonNull(PageInfo), resolve=default_resolver),
            "totalCount": Field(NonNull(Int), resolve=default_resolver),
        }

    return_type = ConnectionType(name=name, fields=build_attrs, description="", sqla_model=sqla_model)
    return return_type
