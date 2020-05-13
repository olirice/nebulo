from functools import lru_cache

from nebulo.config import Config
from nebulo.gql.alias import EdgeType, Field

__all__ = ["edge_factory"]


@lru_cache()
def edge_factory(sqla_model):
    name = Config.table_name_mapper(sqla_model) + "Edge"

    def build_attrs():
        from .table import table_factory
        from .cursor import Cursor

        return {"cursor": Field(Cursor), "node": Field(table_factory(sqla_model))}

    edge = EdgeType(name=name, fields=build_attrs, description="")
    edge.sqla_model = sqla_model
    return edge
