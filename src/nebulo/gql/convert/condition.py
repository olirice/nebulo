from __future__ import annotations

import typing
from functools import lru_cache

from nebulo.gql.alias import InputObjectType
from nebulo.gql.convert.column import convert_column_to_input
from nebulo.gql.convert.factory_config import FactoryConfig

if typing.TYPE_CHECKING:
    from nebulo.sql.table_base import TableBase

__all__ = ["condition_factory"]


@lru_cache()
def condition_factory(sqla_model: TableBase) -> InputObjectType:
    result_name = f"{FactoryConfig.table_name_mapper(sqla_model)}Condition"
    attrs = {}
    for column in sqla_model.__table__.columns:
        field_key = FactoryConfig.column_name_mapper(column)
        attrs[field_key] = convert_column_to_input(column)
    return InputObjectType(result_name, attrs, description="")
