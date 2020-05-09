from functools import lru_cache

from nebulo.gql.alias import EdgeType, Field
from nebulo.gql.convert.factory_config import FactoryConfig

__all__ = ["edge_factory"]


@lru_cache()
def edge_factory(sqla_model):
    name = FactoryConfig.table_name_mapper(sqla_model) + "Edge"

    def build_attrs():
        from .table import table_factory
        from .cursor import Cursor

        return {"cursor": Field(Cursor), "node": Field(table_factory(sqla_model))}

    edge = EdgeType(name=name, fields=build_attrs, description="")
    edge.sqla_model = sqla_model
    return edge
