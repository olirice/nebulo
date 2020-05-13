# pylint: disable=missing-class-docstring,invalid-name
import typing

from graphql.language import ObjectTypeDefinitionNode, ObjectTypeExtensionNode
from graphql.type import (
    GraphQLArgument,
    GraphQLBoolean,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLFieldMap,
    GraphQLID,
    GraphQLInputObjectType,
    GraphQLInt,
    GraphQLInterfaceType,
    GraphQLIsTypeOfFn,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLResolveInfo,
    GraphQLScalarType,
    GraphQLSchema,
    GraphQLString,
    GraphQLType,
    Thunk,
)
from nebulo.sql.composite import CompositeType as SQLACompositeType

# Handle name changes from graphql-core and graphql-core-next
try:
    from graphql.type import GraphQLInputObjectField as GraphQLInputField
except ImportError:
    from graphql.type import GraphQLInputField

Type = GraphQLType
List = GraphQLList
NonNull = GraphQLNonNull
Argument = GraphQLArgument
Boolean = GraphQLBoolean
String = GraphQLString
ScalarType = GraphQLScalarType
ID = GraphQLID
InterfaceType = GraphQLInterfaceType
Int = GraphQLInt
InputObjectType = GraphQLInputObjectType
InputField = GraphQLInputField
ResolveInfo = GraphQLResolveInfo
EnumType = GraphQLEnumType
EnumValue = GraphQLEnumValue
Schema = GraphQLSchema
Field = GraphQLField


class HasSQLAModel:  # pylint: disable= too-few-public-methods
    sqla_table = None


class HasSQLFunction:  # pylint: disable= too-few-public-methods
    sql_function = None


class HasSQLAComposite:  # pylint: disable= too-few-public-methods
    sqla_composite: SQLACompositeType


class ObjectType(GraphQLObjectType, HasSQLAModel):
    def __init__(
        self,
        name: str,
        fields: Thunk[GraphQLFieldMap],
        interfaces: typing.Optional[Thunk[typing.Collection["GraphQLInterfaceType"]]] = None,
        is_type_of: typing.Optional[GraphQLIsTypeOfFn] = None,
        extensions: typing.Optional[typing.Dict[str, typing.Any]] = None,
        description: typing.Optional[str] = None,
        ast_node: typing.Optional[ObjectTypeDefinitionNode] = None,
        extension_ast_nodes: typing.Optional[typing.Collection[ObjectTypeExtensionNode]] = None,
        sqla_model=None,
    ) -> None:
        super().__init__(
            name=name,
            fields=fields,
            interfaces=interfaces,
            is_type_of=is_type_of,
            extensions=extensions,
            description=description,
            ast_node=ast_node,
            extension_ast_nodes=extension_ast_nodes,
        )
        self.sqla_model = sqla_model


class ConnectionType(ObjectType):
    pass


class EdgeType(ObjectType):
    pass


class TableType(ObjectType):
    pass


class CompositeType(ObjectType, HasSQLAComposite):
    pass
