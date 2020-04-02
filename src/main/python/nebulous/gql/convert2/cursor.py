# pylint: disable=comparison-with-callable
from __future__ import annotations

import typing

from sqlalchemy.sql.elements import UnaryExpression
from sqlalchemy.sql.operators import asc_op, desc_op

from ..alias import ScalarType
from ..string_encoding import from_base64, to_base64

__all__ = ["Cursor"]


if typing.TYPE_CHECKING:
    pass


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


def from_cursor(cursor: str):
    cursor_str = from_base64(cursor)
    sqla_model_name, pkey_value, *ordering_str_list = cursor_str.split(":", 2)
    return sqla_model_name, pkey_value, ordering_str_list


Cursor = ScalarType(
    "Cursor", serialize=str, parse_value=from_cursor, parse_literal=lambda x: from_cursor(x.value)
)


def op_to_str(op: UnaryExpression) -> str:
    modifier = op.modifier
    if modifier == asc_op:
        return "A"  # ascending
    if modifier == desc_op:
        return "D"  # descending
    raise ValueError("Unknown direction operator")


def str_to_op(op_str: str) -> UnaryExpression:
    if op_str == "A":
        return asc_op
    if op_str == "D":
        return desc_op
    raise ValueError("Unknown direction str")
