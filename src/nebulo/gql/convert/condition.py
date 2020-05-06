from __future__ import annotations

import typing
from functools import lru_cache

from nebulo.gql.alias import InputObjectType
from nebulo.gql.convert.column import convert_column_to_input
from nebulo.text_utils import snake_to_camel

if typing.TYPE_CHECKING:
    from nebulo.sql.table_base import TableBase

__all__ = ["condition_factory"]


@lru_cache()
def condition_factory(sqla_model: TableBase) -> InputObjectType:

    result_name = f"{snake_to_camel(sqla_model.__table__.name)}Condition"
    attrs = {}
    for column in sqla_model.__table__.columns:
        attrs[column.key] = convert_column_to_input(column)
    return InputObjectType(result_name, attrs, description="")
