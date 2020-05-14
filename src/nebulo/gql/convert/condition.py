from __future__ import annotations

from functools import lru_cache

from nebulo.config import Config
from nebulo.gql.alias import InputObjectType
from nebulo.gql.convert.column import convert_column_to_input
from nebulo.sql.inspect import get_columns
from nebulo.sql.table_base import TableProtocol

__all__ = ["condition_factory"]


@lru_cache()
def condition_factory(sqla_model: TableProtocol) -> InputObjectType:
    result_name = f"{Config.table_name_mapper(sqla_model)}Condition"

    attrs = {}
    for column in get_columns(sqla_model):
        field_key = Config.column_name_mapper(column)
        attrs[field_key] = convert_column_to_input(column)
    return InputObjectType(result_name, attrs, description="")
