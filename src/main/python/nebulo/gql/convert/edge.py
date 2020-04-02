from nebulo.gql.alias import EdgeType, Field
from nebulo.text_utils import snake_to_camel

__all__ = ["edge_factory"]


def edge_factory(sqla_model):
    name = f"{snake_to_camel(sqla_model.__table__.name)}Edge"

    def build_attrs():
        from .table import table_factory
        from .cursor import Cursor

        return {"cursor": Field(Cursor), "node": Field(table_factory(sqla_model))}

    edge = EdgeType(name=name, fields=build_attrs, description="")
    edge.sqla_model = sqla_model
    return edge
