from __future__ import annotations

import typing
from functools import lru_cache

from sqlalchemy.sql.elements import UnaryExpression

from ..alias import (
    Argument,
    EnumType,
    EnumValue,
    Field,
    InputField,
    InputObjectType,
    Int,
    List,
    NonNull,
    ObjectType,
)
from ..casing import snake_to_camel
from .base import TableToGraphQLField
from .cursor import Cursor
from .edge import Edge
from .page_info import PageInfo
from .table import Table
from .total_count import TotalCount

if typing.TYPE_CHECKING:
    from ..alias import ResolveInfo
    from nebulous.sql.table_base import TableBase

__all__ = ["Connection"]

ast = {}


class Connection(TableToGraphQLField):
    def __init__(self, sqla_model):
        super().__init__(sqla_model)
        self.page_info = PageInfo(sqla_model)
        self.total_count = TotalCount(sqla_model)
        self.edge = Edge(sqla_model)
        self.table = Table(sqla_model)
        # self.order_by = table_to_order_by(sqla_model)
        self.condition = table_to_condition(sqla_model)
        self.cursor = Cursor(sqla_model)

    @property
    def type_name(self):
        return f"{snake_to_camel(self.sqla_model.__table__.name)}Connection"

    @property
    def arguments(self):
        sqla_model = self.sqla_model
        # Input Arguments
        args = {
            "first": Argument(Int, default_value=10, description="", out_name=None),
            "last": Argument(Int),
            "before": Argument(self.cursor.type),
            "after": Argument(self.cursor.type),
            "condition": Argument(self.condition),
        }
        return args

    @property
    def _type(self):
        sqla_model = self.sqla_model

        def build_attrs():
            return {
                "nodes": self.table.field(as_nonnull_list=True),
                "edges": self.edge.field(nullable=False, as_nonnull_list=True),
                "pageInfo": self.page_info.field(nullable=False),
                "totalCount": self.total_count.field(nullable=False),
            }

        return ObjectType(name=self.type_name, fields=build_attrs, description="")

    def _resolver(self, obj, info: ResolveInfo, **kwargs):

        print("TEST", self.field().sqla_model)

        ast["info"] = info
        ast["connection"] = self
        return {}  # {"nodes": {}}  # {

        # "nodes": [],
        # "edges": {},
        # "totalCount": None,
        # }


def table_to_default_ordering(sqla_model: TableBase) -> typing.List[UnaryExpression]:
    """Default ordering for tables to ensure cursors return correct data
    1. Currently using primary
    2. Failing over to any unique index
    3. Failing over to all columns in order

    Use this list of columns as the orderby clause when a table is queried
    """
    pkey = sqla_model.primary_key
    if pkey is not None:
        return [x.desc() for x in pkey]

    uconsts = sqla_model.unique_constraints
    for uconst in uconsts:
        return [x.desc() for x in uconst]

    return [x.desc() for x in sqla_model.columns]


@lru_cache()
def table_to_condition(sqla_model: TableBase) -> InputObjectType:
    from nebulous.gql.convert.table import convert_column

    result_name = f"{snake_to_camel(sqla_model.__table__.name)}Condition"
    attrs = {}
    for column in sqla_model.columns:
        attrs[column.name] = convert_column(column, output_type=InputField)
    return InputObjectType(result_name, attrs, description="", container_type=None)


@lru_cache()
def table_to_order_by(sqla_model: TableBase) -> InputObjectType:
    result_name = f"{snake_to_camel(sqla_model.__table__.name)}OrderBy"
    # TODO(OR): Implement properly
    return EnumType(result_name, {"ID_DESC": EnumValue(value=("id", "desc"))}, description="")
