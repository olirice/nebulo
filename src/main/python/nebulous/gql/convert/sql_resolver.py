# pylint: disable=invalid-name
from __future__ import annotations

from sqlalchemy import func, literal, select
from sqlalchemy.orm import interfaces

from .table import relationship_to_attr_name


def resolve_one(tree, parent_query: "cte", result_wrapper=func.json_build_object) -> "SelectClause":
    """Builds select and where clauses for queries"""

    return_type = tree["return_type"]

    sqla_model = return_type.sqla_model

    query = parent_query if parent_query is not None else return_type.sqla_model.__table__.alias()

    # Maps graphql model attribute to sqla relationship
    relation_map = {relationship_to_attr_name(rel): rel for rel in sqla_model.relationships}

    fields = tree["fields"]

    # Always return the table name in each row
    builder = [literal("_table_name"), literal(sqla_model.__table__.name)]

    for tree_field in fields:
        field_name = tree_field["name"]
        field_alias = tree_field["alias"]

        # Handle basic attribute access case
        if hasattr(sqla_model, field_name):
            builder.extend([literal(field_alias), getattr(query.c, field_name)])

        # Handle NodeID case
        elif field_name == "nodeId":
            # Move this into node_interface
            raise NotImplementedError("Not implemented NodeID")

        # Handle Relationships
        elif field_name in relation_map.keys():
            relation = relation_map[field_name]
            # Table we're joinig to
            joined_table = list(relation.remote_side)[0].table.alias()

            # Build where conditions to implement a join
            join_conditions = []
            for local_col, remote_col in relation.local_remote_pairs:
                join_conditions.extend(
                    [
                        getattr(parent_query.c, local_col.name)
                        == getattr(joined_table.c, remote_col.name)
                    ]
                )

            # Many to One relationship
            if relation.direction == interfaces.MANYTOONE:
                # To-One relationships don't have where clauses
                select_clause = resolve_one(tree_field, parent_query=joined_table)
                builder.extend(
                    [
                        literal(field_alias),
                        select([select_clause]).where(*join_conditions).label("q"),
                    ]
                )

            # To Many relationship
            elif relation.direction in (interfaces.ONETOMANY, interfaces.MANYTOMANY):
                from .connection import resolve_connection

                select_clause = resolve_connection(tree_field, parent_query=joined_table)
                selector = select([select_clause]).where(*join_conditions)

                builder.extend([literal(field_alias), selector.label("w")])
            else:
                raise NotImplementedError(f"Unknown relationship type {relation.direction}")

        else:
            raise NotImplementedError(f"Unreachable. No field {field_name} on connection")

    return result_wrapper(*builder)
