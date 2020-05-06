# pylint: disable=missing-class-docstring,invalid-name
from graphql.type import (
    GraphQLArgument,
    GraphQLBoolean,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLID,
    GraphQLInputObjectType,
    GraphQLInt,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLResolveInfo,
    GraphQLScalarType,
    GraphQLSchema,
    GraphQLString,
    GraphQLType,
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
    pass


class ConnectionType(ObjectType, HasSQLAModel):
    pass


class EdgeType(ObjectType, HasSQLAModel):
    pass


class TableType(ObjectType, HasSQLAModel):
    pass


class CompositeType(ObjectType, HasSQLAComposite):
    pass
