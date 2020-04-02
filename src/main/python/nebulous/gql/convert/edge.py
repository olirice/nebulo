from graphql.pyutils.convert_case import snake_to_camel

from ..alias import Field, ObjectType
from .base import TableToGraphQLField
from .page_info import CursorType

__all__ = ["Edge"]


class Edge(TableToGraphQLField):
    @property
    def type_name(self):
        return f"{snake_to_camel(self.sqla_model.__table__.name)}Edge"

    @property
    def _type(self):
        def build_attrs():
            from nebulous.gql.converter import table_to_model

            return {"cursor": Field(CursorType), "node": Field(table_to_model(self.sqla_model))}

        return ObjectType(name=self.type_name, fields=build_attrs, description="")

    def resolver(self, obj, info, **user_kwargs):
        print("Resolving edge")
        sqla_model = self.sqla_model
        context = info.context
        session = context["session"]

        return None
