from ..alias import Boolean, Field, NonNull, ObjectType
from ..casing import snake_to_camel
from .base import TableToGraphQLField
from .cursor import Cursor

__all__ = ["PageInfo"]


class PageInfo(TableToGraphQLField):
    @property
    def type_name(self):
        return f"{snake_to_camel(self.sqla_model.__table__.name)}PageInfo"

    @property
    def _type(self):
        sqla_model = self.sqla_model
        cursor = Cursor(self.sqla_model)

        def build_attrs():
            return {
                "hasNextPage": Field(NonNull(Boolean)),
                "hasPreviousPage": Field(NonNull(Boolean)),
                "startCursor": cursor.field(nullable=False),  # Field(NonNull(Cursor._type)),
                "endCursor": cursor.field(nullable=False),  # Field(NonNull(Cursor._type)),
            }

        return ObjectType(name=self.type_name, fields=build_attrs, description="")

    def _resolver(self, obj, info, **user_kwargs):
        sqla_model = self.sqla_model
        sqla_model = sqla_model

        return {
            "hasNextPage": False,
            "hasPreviousPage": False,
            # "startCursor": "Unknown",
            # "endCursor": "Unknown",
        }
