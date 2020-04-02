from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
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
            "orderBy": Argument(List(NonNull(model_order_by)), default_value=["ID_DESC"]),
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

    def resolver(self, obj, info: ResolveInfo, **user_kwargs):
        print("Connection", info.path, info.return_type, "\n\t", obj, "\n\t", user_kwargs)
        sqla_model = self.sqla_model
        context = info.context
        session = context["session"]
        return_type = info.return_type
        sqla_result = session.query(sqla_model).all()
        return {"nodes": sqla_result}


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
