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
from .edge import Edge
from .page_info import CursorType, PageInfo
from .table import Table
from .total_count import TotalCount

if typing.TYPE_CHECKING:
    from ..alias import ResolveInfo
    from nebulous.sql.table_base import TableBase

__all__ = ["Connection"]


class Connection(TableToGraphQLField):
    @property
    def type_name(self):
        return f"{snake_to_camel(self.sqla_model.__table__.name)}Connection"

    @property
    def arguments(self):
        sqla_model = self.sqla_model
        # Input Arguments
        model_order_by = table_to_order_by(sqla_model)
        model_condition = table_to_condition(sqla_model)
        args = {
            "first": Argument(Int, default_value=10, description="", out_name=None),
            "last": Argument(Int),
            "offset": Argument(Int, description="Alternative to cursor pagination"),
            "before": Argument(CursorType),
            "after": Argument(CursorType),
            # "orderBy": Argument(List(NonNull(model_order_by)), default_value=["ID_DESC"]),
            "condition": Argument(model_condition),
        }
        return args

    @property
    def _type(self):
        sqla_model = self.sqla_model

        page_info = PageInfo(sqla_model)
        total_count = TotalCount(sqla_model)
        edge = Edge(sqla_model)
        table = Table(sqla_model)

        def build_attrs():
            return {
                "nodes": table.field(as_nonnull_list=True),
                "pageInfo": page_info.field(nullable=False),
                "edges": edge.field(nullable=False, as_nonnull_list=True),
                "totalCount": total_count.field(nullable=False),
            }

        return ObjectType(name=self.type_name, fields=build_attrs, description="")

    def resolver(
        self,
        obj,
        info: ResolveInfo,
        first=10,
        last=None,
        offset=0,
        before=None,
        after=None,
        orderBy=None,
        condition=None,
    ):
        print("Connection", info.path, info.return_type, "\n\t", obj, "\n\t")
        sqla_model = self.sqla_model
        context = info.context
        session = context["session"]
        return_type = info.return_type
        sqla_result = session.query(sqla_model).all()

        from sqlalchemy import func
        from sqlalchemy.sql.expression import literal

        # Arguments
        cte_key = ".".join(info.path) + "_args"
        args_cte = session.query(
            literal(first).label("first"),
            literal(last).label("last"),
            literal(offset).label("offset"),
            literal(before).label("before"),
            literal(after).label("after"),
            # literal(orderBy).label("orderby"),
        ).cte(cte_key)
        context[cte_key] = args_cte

        # Nodes
        cte_key = ".".join(info.path) + "_nodes"
        nodes_cte = session.query(self.sqla_model)

        # Apply Conditions
        if condition is not None:
            for key, val in condition.items():
                nodes_cte = nodes_cte.filter(getattr(sqla_model, key) == val)

        # Apply Ordering
        if orderBy is not None:
            orderdict = {"ID_DESC": self.sqla_model.id.desc(), "ID_ASC": self.sqla_model.id.asc()}
            q_orderby = [orderdict[x] for x in orderBy]
            # For pagination, we must force a constant ordering
            default_ordering = table_to_default_ordering(sqla_model)
            q_orderby.extendappend(default_ordering)
            nodes_cte = nodes_cte.order_by(*q_orderby)

        # Apply Offset
        if offset is not None:
            nodes_cte = nodes_cte.offset(offset)

        # Avoid footgun scenario with sane limit clause
        if offset is not None:
            nodes_cte = nodes_cte.limit(150)
        nodes = nodes_cte.cte(cte_key)
        context[cte_key] = nodes_cte
        print("Nodes:", session.query(nodes).all())

        # totalCount
        cte_key = ".".join(info.path) + "_total_count"
        total_cte = session.query(func.count(self.sqla_model.columns[0]))

        # Apply Conditions
        if condition is not None:
            for key, val in condition.items():
                total_cte = total_cte.filter(getattr(sqla_model, key) == val)

        # Apply Ordering
        if orderBy is not None:
            orderdict = {"ID_DESC": self.sqla_model.id.desc(), "ID_ASC": self.sqla_model.id.asc()}
            q_orderby = [orderdict[x] for x in orderBy]
            # For pagination, we must force a constant ordering
            default_ordering = table_to_default_ordering(sqla_model)
            q_orderby.extendappend(default_ordering)
            total_cte = total_cte.order_by(*q_orderby)

        total_cte = total_cte.cte(cte_key)
        context[cte_key] = total_cte
        print("TotalCount:", session.query(total_cte).all())

        return {
            "nodes": session.query(nodes).all(),
            "pageInfo": {},
            "edges": {},
            "totalCount": session.query(total_cte).one(),
        }


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
