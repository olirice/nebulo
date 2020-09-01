import typing

from graphql.execution.execute import get_field_def
from graphql.execution.values import get_argument_values
from graphql.language import FieldNode, FragmentDefinitionNode, FragmentSpreadNode, InlineFragmentNode
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
    def __init__(
        self,
        field_node: FieldNode,
        field_def: ObjectType,
        schema: Schema,
        parent: typing.Optional["ASTNode"],
        variable_values,
        parent_type,
        fragments: typing.Dict[str, FragmentDefinitionNode],
    ):
        self.name = field_node.name.value

        # A connection/edge/etc class
        field_def = get_field_def(schema, parent_type, self.name)

        _args = get_argument_values(type_def=field_def, node=field_node, variable_values=variable_values)

        selection_set = field_node.selection_set
        field_type = field_to_type(field_def)

        self.alias = (field_node.alias.value if field_node.alias else None) or field_node.name.value
        self.return_type = field_type
        self.parent: typing.Optional[ASTNode] = parent
        self.parent_type = parent_type
        self.args: typing.Dict[str, typing.Any] = _args
        self.path: typing.List[str] = parent.path + [self.name] if parent is not None else ["root"]

        def from_selection_set(selection_set):
            for selection_ast in selection_set.selections:

                # Handle fragments
                if isinstance(selection_ast, FragmentSpreadNode):
                    fragment_name = selection_ast.name.value
                    fragment = fragments[fragment_name]
                    fragment_selection_set = fragment.selection_set
                    yield from from_selection_set(fragment_selection_set)

                elif isinstance(selection_ast, InlineFragmentNode):
                    yield from from_selection_set(selection_ast.selection_set)

                else:
                    selection_name = selection_ast.name.value
                    if selection_name.startswith("__"):
                        # Reserved "introspection" field handled by framework
                        continue
                    selection_field = field_type.fields[selection_name]
                    yield ASTNode(
                        field_node=selection_ast,
                        field_def=selection_field,
                        schema=schema,
                        parent=self,
                        variable_values=variable_values,
                        parent_type=field_type,
                        fragments=fragments,
                    )

        sub_fields = list(from_selection_set(selection_set)) if selection_set else []
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
    field_node = info.field_nodes[0]
    schema = info.schema

    fragments: typing.Dict[str, FragmentDefinitionNode] = info.fragments

    # Current field from parent
    parent_type = info.parent_type
    parent_lookup_name = field_node.name.value
    current_field = parent_type.fields[parent_lookup_name]
    parsed_info = ASTNode(
        field_node,
        current_field,
        schema,
        parent=None,
        variable_values=info.variable_values,
        parent_type=info.parent_type,
        fragments=fragments,
    )
    return parsed_info
