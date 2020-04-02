from ..alias import EdgeType, Field
from ..casing import snake_to_camel

__all__ = ["edge_factory"]


def edge_factory(sqla_model):
    name = f"{snake_to_camel(sqla_model.__table__.name)}Edge"

    def build_attrs():
        from .table import table_factory
        from .cursor import Cursor

        return {"cursor": Field(Cursor), "node": Field(table_factory(sqla_model))}

    return EdgeType(name=name, fields=build_attrs, description="")
