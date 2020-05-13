from functools import lru_cache

from nebulo.config import Config
from nebulo.gql.alias import EdgeType, Field

__all__ = ["edge_factory"]


@lru_cache()
def edge_factory(sqla_model):
    from .cursor import Cursor
    from .table import table_factory

    name = Config.table_name_mapper(sqla_model) + "Edge"

    def build_attrs():
        return {"cursor": Field(Cursor), "node": Field(table_factory(sqla_model))}

    edge = EdgeType(name=name, fields=build_attrs, description="", sqla_model=sqla_model)
    return edge
