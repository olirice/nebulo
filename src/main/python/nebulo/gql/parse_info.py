import typing

from graphql.execution.values import get_argument_values
from nebulo.gql.alias import Field, List, NonNull, ObjectType, ResolveInfo, Schema

__all__ = ["parse_resolve_info"]


def field_to_type(field):
    """Recursively unwraps nested Field, List, and NonNull
    qualifiers to a concrete GraphQL Type"""
    if isinstance(field, Field):
        return field_to_type(field.type)
    if isinstance(field, List):
        return field_to_type(field.of_type)
    if isinstance(field, NonNull):
        return field_to_type(field.of_type)
    return field


class ASTNode:
    def __init__(self, field_ast: Field, field_def: ObjectType, schema: Schema, parent: typing.Optional["ASTNode"]):

        args = get_argument_values(arg_defs=field_def.args, arg_asts=field_ast.arguments)
        selection_set = field_ast.selection_set
        field_type = field_to_type(field_def)

        self.alias = (field_ast.alias.value if field_ast.alias else None) or field_ast.name.value
        self.name = field_ast.name.value
        self.return_type = field_type
        self.parent: typing.Optional[ASTNode] = parent
        self.args: typing.Dict[str, typing.Any] = args
        self.path: typing.List[str] = parent.path + [self.name] if parent is not None else ["root"]

        sub_fields = []
        if selection_set:
            for selection_ast in selection_set.selections:
                selection_name = selection_ast.name.value
                selection_field = field_type.fields[selection_name]
                sub_fields.append(ASTNode(selection_ast, selection_field, schema, parent=self))

        self.fields = sub_fields

    def get_subfield_alias(self, path: typing.List[str]):
        """Searches subfields by name returning the alias
        for the terminating element in *path* list. If that subfield
        is not in the selection set, return the terminating elements name"""
        if len(path) < 1:
            raise Exception("Path must contain an element")

        for subfield in self.fields:
            if subfield.name == path[0]:
                if len(path) == 1:
                    return subfield.alias or path[0]
                return subfield.get_subfield_alias(path[1:])
        return path[-1]


def parse_resolve_info(info: ResolveInfo) -> ASTNode:
    """Converts execution ResolveInfo into a dictionary
    hierarchy

    {
        "alias": *alias*,
        "name": *name*,
        "return_type": *return_type*,
        "args":  {
            "first": 10
        },
        "parent": <reference to parent field or None>
        "fields": [
            # Same structure again, for each field selected
            # in the query
            {
                "alias": ...
                "name": ...
            }
        }
    }
    """
    # Root info
    field_ast = info.field_asts[0]
    schema = info.schema

    # Current field from parent
    parent_type = info.parent_type
    parent_lookup_name = field_ast.name.value
    current_field = parent_type.fields[parent_lookup_name]

    parsed_info = ASTNode(field_ast, current_field, schema, parent=None)
    return parsed_info
