from nebulo.gql.alias import Boolean, Field, NonNull, ObjectType
from nebulo.gql.convert.cursor import Cursor

__all__ = ["PageInfo"]

PageInfo = ObjectType(
    name="PageInfo",
    fields={
        "hasNextPage": Field(NonNull(Boolean)),
        "hasPreviousPage": Field(NonNull(Boolean)),
        "startCursor": Field(NonNull(Cursor)),
        "endCursor": Field(NonNull(Cursor)),
    },
    description="",
)
