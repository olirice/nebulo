from graphql.pyutils.convert_case import snake_to_camel

from ..alias import Field, List, NonNull, ObjectType
from .base import TableToGraphQLField
from .edge import Edge
from .page_info import PageInfo
from .total_count import TotalCount

__all__ = ["Connection"]


class Connection(TableToGraphQLField):
    @property
    def type_name(self):
        return f"{snake_to_camel(self.sqla_model.__table__.name)}Connection"

    @property
    def _type(self):
        sqla_model = self.sqla_model

        page_info = PageInfo(sqla_model)
        total_count = TotalCount(sqla_model)
        edge = Edge(sqla_model)

        def build_attrs():
            from nebulous.gql.converter import table_to_model

            return {
                "nodes": Field(NonNull(List(table_to_model(sqla_model))), resolver=None),
                "pageInfo": Field(NonNull(page_info.type), resolver=page_info.resolver),
                "edges": Field(NonNull(List(NonNull(edge.type))), resolver=edge.resolver),
                "totalCount": Field(NonNull(total_count.type), resolver=total_count.resolver),
            }

        return ObjectType(name=self.type_name, fields=build_attrs, description="")

    def resolver(self, obj, info, **user_kwargs):
        sqla_model = self.sqla_model
        context = info.context
        session = context["session"]
        return_type = info.return_type
        sqla_result = session.query(sqla_model).all()
        return {"nodes": sqla_result}
