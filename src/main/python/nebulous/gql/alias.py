from graphql.execution import ResolveInfo
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
    GraphQLScalarType,
    GraphQLSchema,
    GraphQLString,
)

# Handle name changes from graphql-core and graphql-core-next
try:
    from graphql.type import GraphQLInputObjectField as GraphQLInputField
except ImportError:
    from graphql.type import GraphQLInputField


Field = GraphQLField
List = GraphQLList
NonNull = GraphQLNonNull
Argument = GraphQLArgument
String = GraphQLString
Boolean = GraphQLBoolean
ScalarType = GraphQLScalarType
ObjectType = GraphQLObjectType
ID = GraphQLID
InterfaceType = GraphQLInterfaceType
Int = GraphQLInt
InputObjectType = GraphQLInputObjectType
InputField = GraphQLInputField
ResolveInfo = ResolveInfo
EnumType = GraphQLEnumType
EnumValue = GraphQLEnumValue
