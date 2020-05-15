# pylint: disable=invalid-name
from __future__ import annotations

import typing

from nebulo.config import Config
from nebulo.gql.parse_info import ASTNode
from nebulo.gql.query_builder import field_name_to_column


def build_insert(tree: ASTNode):
    return_type = tree.return_type
    # Find the table type
    return_sqla_model = return_type.sqla_model
    table_input_arg_name = Config.table_name_mapper(return_sqla_model)
    input_values = tree.args["input"][table_input_arg_name]
    col_name_to_value = {}
    for arg_name, arg_value in input_values.items():
        col = field_name_to_column(return_sqla_model, arg_name)
        col_name_to_value[col.name] = arg_value

    core_table = return_sqla_model.__table__
    query = core_table.insert().values(**col_name_to_value).returning(*core_table.columns)

    return query


def row_to_create_result(tree: ASTNode, row: typing.Dict[str, typing.Any]) -> typing.Dict[str, typing.Any]:
    """
    row is a mapping from col_name -> col_value

    we convert it to field_alias -> col_value

    and append extras like clientMutationID
    """
    return_type = tree.return_type
    # Find the table type
    return_sqla_model = return_type.sqla_model

    result = {}
    for field in tree.fields:
        if field.name == "clientMutationId":
            result[field.alias] = tree.args["input"]["clientMutationId"]
        elif field.name == Config.table_name_mapper(return_sqla_model):
            table_output_alias = field.alias
            result[table_output_alias] = {}
            for col_field in field.fields:
                col = field_name_to_column(return_sqla_model, col_field.name)
                result[table_output_alias][col_field.alias] = row[col.name]
        else:
            raise Exception(f"unexpected return field on create object {field.name}")
    result = {tree.alias: result}

    return result
