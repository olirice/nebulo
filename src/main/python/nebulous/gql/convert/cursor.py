# pylint: disable=comparison-with-callable
from __future__ import annotations

import typing

import sqlalchemy
from sqlalchemy import asc, cast, desc, literal, text

from ..alias import CursorType
from ..string_encoding import from_base64, to_base64, to_base64_sql

__all__ = ["Cursor"]


if typing.TYPE_CHECKING:
    pass


DIRECTION_TO_STR = {asc: "asc", desc: "desc"}
STR_TO_DIRECTION = {v: k for k, v in DIRECTION_TO_STR.items()}


def from_cursor(
    cursor: str
) -> typing.Tuple[str, typing.List[str], typing.List[typing.Tuple[str, "asc/desc"]]]:
    """Parses a cursor from form
    offer[id:desc,age:asc](4)
    """
    cursor_str = from_base64(cursor)

    # e.g. 'offer'
    sqla_model_name, remain = cursor_str.split("[", 1)

    # e.g. 'id:desc,age:asc'
    ordering_str, remain = remain.split("]", 1)
    ordering_elements = [x for x in ordering_str.split(",") if x]
    ordering: typing.Tuple[str, "asc/desc"] = []
    for ordering_element in ordering_elements:
        ordering_col_name, ordering_direction_str = ordering_element.split(":")
        ordering_direction = STR_TO_DIRECTION[ordering_direction_str]
        ordering.append((ordering_col_name, ordering_direction))

    # e.g. '4'
    pkey_values_as_str: typing.List[str] = remain[1:-1].split(",")
    return sqla_model_name, ordering, pkey_values_as_str


Cursor = CursorType(
    "Cursor", serialize=str, parse_value=from_cursor, parse_literal=lambda x: from_cursor(x.value)
)


def resolve_cursor(query, ordering: typing.Tuple[str, "asc/desc"], sqla_model):
    """
    # The 4 is the offer's primary key
    offer[id:desc,age:asc](4)
    """
    # The columns we need to track in order to identify a unique location during pagination
    dir_map = {asc: "asc", desc: "desc"}

    content = literal(sqla_model.__table__.name) + literal("[")

    order_component = literal(
        ",".join([col_name + ":" + dir_map[direction] for col_name, direction in ordering])
    )

    content += order_component
    content += literal("](")

    columns = list(sqla_model.primary_key.columns)
    column_str_builder = []
    for column in columns:
        column_str_builder.append(cast(getattr(query.c, column.name), sqlalchemy.String()))
        column_str_builder.append(literal(","))
    # Remove the final comma. Never realized how useful ''.join is until you can't use it..
    column_str_builder = column_str_builder[:-1]

    for element in column_str_builder:
        content += element

    content += literal(")")

    return to_base64_sql(content)


def to_cursor(sqla_model, sqla_record, ordering: typing.List["UnaryExpr"]) -> str:
    """ SQLA Model name + primary key stopped at + list[index of column names sorted by]"""
    model_name = sqla_model.__table__.name

    # TODO(OR): Support multi column primary keys
    # TODO(OR): Support no primary key
    # Uniquely identify the record
    pkey_attr = list(sqla_model.primary_key.columns)[0].name
    pkey_value = getattr(sqla_record, pkey_attr)

    values = [x.element.name + "," + str(pkey_value) + op_to_str(x) for x in ordering]
    to_encode = ":".join([model_name, *values])
    return to_base64(to_encode)


def to_cursor_sql(sqla_model) -> "sql_selector":
    table_name = sqla_model.table_name
    pkey_cols = list(sqla_model.primary_key.columns)

    selector = ", ||".join([f'"{col.name}"' for col in pkey_cols])

    str_to_encode = f"'{table_name}' || '@' || " + selector

    return to_base64_sql(text(str_to_encode)).compile(compile_kwargs={"literal_binds": True})
