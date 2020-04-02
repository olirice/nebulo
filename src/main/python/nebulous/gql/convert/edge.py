from ..alias import Field, ObjectType
from ..casing import snake_to_camel
from .base import TableToGraphQLField
from .page_info import Cursor

__all__ = ["Edge"]


class Edge(TableToGraphQLField):
    @property
    def type_name(self):
        return f"{snake_to_camel(self.sqla_model.__table__.name)}Edge"

    @property
    def _type(self):
        def build_attrs():
            from .table import Table

            table = Table(self.sqla_model)
            cursor = Cursor(self.sqla_model)

            return {"cursor": Field(cursor.type), "node": table.field()}

        return ObjectType(name=self.type_name, fields=build_attrs, description="")

    def _resolver(self, obj, info, **user_kwargs):
        sqla_model = self.sqla_model
        context = info.context
        session = context["session"]

        return None
