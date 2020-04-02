from ..alias import Int
from .base import TableToGraphQLField

__all__ = ["TotalCount"]


class TotalCount(TableToGraphQLField):

    type_name = "TotalCount"

    _type = Int

    def resolver(self, obj, info, **user_kwargs):
        sqla_model = self.sqla_model
        context = info.context
        session = context["session"]

        return session.query(sqla_model).count()
