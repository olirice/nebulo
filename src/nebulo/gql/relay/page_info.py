from nebulo.gql.alias import Boolean, Field, NonNull, ObjectType
from nebulo.gql.relay.cursor import Cursor

PageInfo = ObjectType(
    name="PageInfo",
    fields={
        "hasNextPage": Field(NonNull(Boolean)),
        "hasPreviousPage": Field(NonNull(Boolean)),
        "startCursor": Field(Cursor),
        "endCursor": Field(Cursor),
    },
    description="",
)
