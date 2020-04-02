# pylint: disable=comparison-with-callable
from __future__ import annotations

import typing

from sqlalchemy.sql.elements import UnaryExpression
from sqlalchemy.sql.operators import asc_op, desc_op

from ..alias import ScalarType
from ..casing import snake_to_camel
from ..string_encoding import from_base64, to_base64
from .base import TableToGraphQLField

__all__ = ["Cursor"]


if typing.TYPE_CHECKING:
    from nebulous.sql.table_base import TableBase


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


class Cursor(TableToGraphQLField):
    """Cursor uniquely identifies a record within a table and a sort order for for that table

    To use a cursor, use the sorting order to sort the query and return records before/after
    the row that is uniquely identified.

    The unique identifier is its primary key value
    """

    @property
    def type_name(self):
        return f"{snake_to_camel(self.sqla_model.__table__.name)}Cursor"

    @property
    def _type(self):
        return ScalarType(
            self.type_name,
            serialize=str,
            parse_value=self.from_cursor,
            parse_literal=lambda x: self.from_cursor(x.value),
        )

    def _resolver(self, obj, info, **kwargs):
        """
        There are 3 ways we can hit this resolver
        1. `cursor` on ModelEdge
        1. `startCursor` on ModelPageInfo
        2. `endCursor` on ModelPageInfo
        """
        path = info.path
        context = info.context
        resolve_type = path[-1]
        sqla_model = self.sqla_model
        sqla_model = sqla_model

        assert resolve_type in ("cursor", "startCursor", "endCursor")

        base_key = ".".join(info.path[:-2])
        ordering_key = base_key + "_ordering"
        ordering = context.get(ordering_key)
        if resolve_type == "startCursor":
            # Find first record in the "nodes" result set
            first_key = base_key + "_first_node"
            first_record = context.get(first_key)
            return to_cursor(self.sqla_model, first_record, ordering=ordering)

        if resolve_type == "endCursor":
            # Find first record in the "nodes" result set
            last_key = base_key + "_last_node"
            last_record = context.get(last_key)
            return to_cursor(self.sqla_model, last_record, ordering=ordering)

        raise NotImplementedError("have not handled cursor type on ModelEdge")

    def from_cursor(self, cursor: str) -> typing.Tuple[TableBase, typing.List[UnaryExpression]]:
        sqla_model = self.sqla_model

        cursor_str = from_base64(cursor)
        sqla_model_name, pkey_value, *ordering_str_list = cursor_str.split(":", 2)

        # Make sure the cursor is of the correct type
        assert sqla_model_name == sqla_model.__table__.name

        ordering_split_str_list: typing.List[typing.Tuple[str, str]] = [
            x.split(",") for x in ordering_str_list
        ]
        ordering = [
            str_to_op(op_str)(getattr(sqla_model, col_name))
            for col_name, op_str in ordering_split_str_list
        ]
        return sqla_model, pkey_value, ordering
