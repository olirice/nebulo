from __future__ import annotations

import typing

from nebulo.gql.alias import Field, InterfaceType, NonNull, ScalarType
from nebulo.sql.inspect import get_table_name
from nebulo.text_utils.base64 import from_base64, to_base64, to_base64_sql
from sqlalchemy import text

if typing.TYPE_CHECKING:
    from sqlalchemy.sql.compiler import StrSQLCompiler


def to_global_id(table_name: str, values: typing.List[typing.Any]) -> str:
    """
    Takes a type name and an ID specific to that type name, and returns a
    "global ID" that is unique among all types.
    """
    return to_base64(table_name + "@" + ",".join([str(x) for x in values]))


def from_global_id(global_id: str) -> typing.Tuple[str, typing.List[str]]:
    """
    Takes the "global ID" created by toGlobalID, and returns the type name and ID
    used to create it.
    """
    try:
        unbased_global_id = from_base64(global_id)
        table_name, values = unbased_global_id.split("@", 1)
        # TODO(OR): Text fields in primary key might contain a comma
        values = values.split(",")
    except Exception:
        raise ValueError(f"Bad input: invalid NodeID {global_id}")
    return table_name, values


def to_global_id_sql(sqla_model) -> StrSQLCompiler:
    table_name = get_table_name(sqla_model)
    pkey_cols = list(sqla_model.__table__.primary_key.columns)

    selector = ", ||".join([f'"{col.name}"' for col in pkey_cols])

    str_to_encode = f"'{table_name}' || '@' || " + selector
    ret_val = to_base64_sql(text(str_to_encode)).compile(compile_kwargs={"literal_binds": True})
    return ret_val


NodeID = ScalarType(
    "NodeID",
    description="Unique ID for node",
    serialize=str,
    parse_value=from_global_id,
    parse_literal=lambda x: from_global_id(global_id=x.value),
)

NodeInterface = InterfaceType(
    "NodeInterface",
    description="An object with a nodeId",
    fields={"nodeId": Field(NonNull(NodeID), description="The global id of the object.", resolver=None)},
    # Maybe not necessary
    resolve_type=lambda *args, **kwargs: None,
)
