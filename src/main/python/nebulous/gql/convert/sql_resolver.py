# pylint: disable=invalid-name
from __future__ import annotations

import typing

import sqlalchemy
from sqlalchemy import asc, cast, desc, func, literal, select
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.orm import interfaces
from sqlalchemy.sql.expression import literal

from .table import relationship_to_attr_name


def encode(text_to_encode, encoding="base64"):
    return func.encode(cast(text_to_encode, BYTEA()), cast(encoding, sqlalchemy.Text()))


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
            builder.extend([literal(field_alias), resolve_node_id(query, sqla_model)])

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
                select_clause, condition_partials = resolve_connection(
                    tree_field, parent_query=joined_table
                )
                selector = select([select_clause]).where(*join_conditions)

                # Apply filters, limits, arguments etc... I don't like it either.
                for partial in condition_partials:
                    print("Applying partial")
                    selector = partial(selector)

                builder.extend([literal(field_alias), selector.label("w")])
            else:
                raise NotImplementedError(f"Unknown relationship type {relation.direction}")

        else:
            raise NotImplementedError(f"Unreachable. No field {field_name} on connection")

    return result_wrapper(*builder)


def resolve_connection(tree, parent_query) -> typing.Tuple["SelectClause", "ConditionPartials"]:
    """Resolves a single record from a table"""
    condition_partials = []

    fields = tree["fields"]

    # Apply Argument Filters
    query = select([parent_query])

    args = tree["args"]

    order_by = args.get("orderBy")
    if order_by is not None:
        order_clause = [direction(getattr(query.c, col_name)) for col_name, direction in order_by]
        query = query.order_by(*order_clause)

    # Allowed Args [first, last, ordering?, etc]
    first = args.get("first")
    if first is not None:
        query = query.limit(first)

    query = query.alias()

    # Always return the table name in each row
    builder = []

    for tree_field in fields:
        field_name = tree_field["name"]
        field_alias = tree_field["alias"]

        if field_name == "nodes":
            result_wrapper = lambda *x: func.json_agg(func.json_build_object(*x))
            builder.extend(
                [
                    literal(field_alias),
                    resolve_one(tree_field, query, result_wrapper=result_wrapper),
                ]
            )

        elif field_name == "edges":

            edge_builder = []
            edge_fields = tree_field["fields"]

            for edge_field in edge_fields:
                if edge_field["name"] == "node":
                    edge_field_alias = edge_field["alias"]
                    edge_builder.extend(
                        [
                            literal(edge_field_alias),  # nodes
                            # node query
                            resolve_one(edge_field, query, result_wrapper=func.json_build_object),
                        ]
                    )
                if edge_field["name"] == "cursor":
                    edge_field_alias = edge_field["alias"]
                    edge_builder.extend(
                        [
                            literal(edge_field_alias),
                            resolve_cursor(
                                query,
                                ordering=order_by or [],
                                sqla_model=tree["return_type"].sqla_model,
                            ),
                        ]
                    )

            builder.extend(
                [literal(field_alias), func.array_agg(func.json_build_object(*edge_builder))]
            )

        elif field_name == "pageInfo":
            print("Delegating for page info")

        else:
            raise NotImplementedError(f"Unreachable. No field {field_name} on connection")

    return func.json_build_object(*builder), condition_partials


def resolve_node_id(query, sqla_model):
    return encode(
        literal(sqla_model.__table__.name) + literal(":") + cast(query.c.id, sqlalchemy.String())
    )


def resolve_cursor(query, ordering: typing.Tuple[str, "asc/desc"], sqla_model):
    """
    # The 4 is the offer's primary key
    offer[id:desc,age:asc](4)
    """
    # The columns we need to track in order to identify a unique location during pagination
    dir_map = {asc: "asc", desc: "desc"}

    content = literal(sqla_model.__table__.name) + literal("[")

    order_component = literal(
        ",".join([col_name + ":" + dir_map[direction] for col_name, direction in ordering])
    )

    content += order_component
    content += literal("](")

    columns = list(sqla_model.primary_key.columns)
    for column in columns:
        content += cast(getattr(query.c, column.name), sqlalchemy.String())
        content += literal(",")

    content += literal(")")

    return encode(content)
