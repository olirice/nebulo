from __future__ import annotations

import json
import typing

from nebulo.gql.alias import Field, InterfaceType, NonNull, ScalarType
from nebulo.sql.inspect import get_primary_key_columns, get_table_name
from nebulo.text_utils.base64 import from_base64, to_base64
from sqlalchemy import func, literal
from sqlalchemy.sql.selectable import Alias

if typing.TYPE_CHECKING:
    pass


class NodeIdStructure(typing.NamedTuple):
    table_name: str
    values: typing.Dict[str, typing.Any]

    @classmethod
    def from_dict(cls, contents: typing.Dict) -> NodeIdStructure:
        res = cls(table_name=contents["table_name"], values=contents["values"])
        return res

    def to_dict(self) -> typing.Dict[str, typing.Any]:
        return {"table_name": self.table_name, "values": self.values}

    def serialize(self) -> str:
        ser = to_base64(json.dumps(self.to_dict()))
        return ser

    @classmethod
    def deserialize(cls, serialized: str) -> NodeIdStructure:
        contents = json.loads(from_base64(serialized))
        return cls.from_dict(contents)


def serialize(value: typing.Union[NodeIdStructure, typing.Dict]):
    node_id = NodeIdStructure.from_dict(value) if isinstance(value, dict) else value
    return node_id.serialize()


def to_node_id_sql(sqla_model, query_elem: Alias):
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


NodeID = ScalarType(
    "NodeID",
    description="Unique ID for node",
    serialize=serialize,
    parse_value=NodeIdStructure.deserialize,
    parse_literal=lambda x: NodeIdStructure.deserialize(x.value),
)

NodeInterface = InterfaceType(
    "NodeInterface",
    description="An object with a nodeId",
    fields={"nodeId": Field(NonNull(NodeID), description="The global id of the object.", resolve=None)},
    # Maybe not necessary
    resolve_type=lambda *args, **kwargs: None,
)
