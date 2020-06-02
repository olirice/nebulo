# pylint: disable=comparison-with-callable
from __future__ import annotations

import json
import typing

from nebulo.gql.alias import ScalarType
from nebulo.sql.inspect import get_primary_key_columns, get_table_name
from nebulo.text_utils.base64 import from_base64, to_base64
from sqlalchemy import func, literal
from sqlalchemy.sql.selectable import Alias

__all__ = ["Cursor"]


class CursorStructure(typing.NamedTuple):
    table_name: str
    values: typing.Dict[str, typing.Any]

    @classmethod
    def from_dict(cls, contents: typing.Dict) -> CursorStructure:
        res = cls(table_name=contents["table_name"], values=contents["values"])
        return res

    def to_dict(self) -> typing.Dict[str, typing.Any]:
        return {"table_name": self.table_name, "values": self.values}

    def serialize(self) -> str:
        ser = to_base64(json.dumps(self.to_dict()))
        return ser

    @classmethod
    def deserialize(cls, serialized: str) -> CursorStructure:
        contents = json.loads(from_base64(serialized))
        return cls.from_dict(contents)


def serialize(value: typing.Union[CursorStructure, typing.Dict]):
    node_id = CursorStructure.from_dict(value) if isinstance(value, dict) else value
    return node_id.serialize()


def to_cursor_sql(sqla_model, query_elem: Alias):
    table_name = get_table_name(sqla_model)

    pkey_cols = get_primary_key_columns(sqla_model)

    # Columns selected from query element
    vals = []
    for col in pkey_cols:
        col_name = str(col.name)
        vals.extend([col_name, query_elem.c[col_name]])

    return func.jsonb_build_object(
        literal("table_name"), literal(table_name), literal("values"), func.jsonb_build_object(*vals)
    )


Cursor = ScalarType(
    "Cursor",
    description="Pagination point",
    serialize=serialize,
    parse_value=CursorStructure.deserialize,
    parse_literal=lambda x: CursorStructure.deserialize(x.value),
)
