from ..alias import Boolean, Field, NonNull, ObjectType, ScalarType
from .base import TableToGraphQLField

__all__ = ["PageInfo"]

CursorType = ScalarType(name="Cursor", serialize=str)  # pylint: disable=invalid-name


class PageInfo(TableToGraphQLField):

    type_name = "PageInfo"

    _type = ObjectType(  # pylint: disable=invalid-name
        "PageInfo",
        fields={
            "hasNextPage": Field(NonNull(Boolean)),
            "hasPreviousPage": Field(NonNull(Boolean)),
            "startCursor": Field(NonNull(CursorType)),
            "endCursor": Field(NonNull(CursorType)),
        },
    )

    def resolver(self, obj, info, **user_kwargs):
        print(info.path, info.return_type, "\n\t", obj, info.context)
        sqla_model = self.sqla_model
        sqla_model = sqla_model

        return {
            "hasNextPage": False,
            "hasPreviousPage": False,
            "startCursor": "Unknown",
            "endCursor": "Unknown",
        }
